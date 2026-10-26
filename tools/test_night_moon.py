"""GPU checks for the analytic moon.

The fixture renders a narrow synthetic view (3 degree half-FOV) around the
zenith moon and samples moonSky() directly, so the assertions describe the
phase terminator, surface structure, halo and weather gate without the galaxy
band or atmosphere gradient masking the result. The call site is covered by
the compile/render suites. This is not a Minecraft capture.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W = H = 256
HALF_FOV = np.radians(3.0)
DISK_ANGLE = np.radians(1.9)
DISK_RADIUS = np.tan(DISK_ANGLE) / np.tan(HALF_FOV)

VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
yy, xx = np.mgrid[0:H, 0:W]
PX = (xx + 0.5) / W * 2.0 - 1.0
PY = (yy + 0.5) / H * 2.0 - 1.0
RR = np.sqrt(PX * PX + PY * PY)
DISK = RR < 0.75 * DISK_RADIUS        # comfortably inside the limb
QUARTER = RR < 0.94 * DISK_RADIUS
HALO = (RR > 1.10 * DISK_RADIUS) & (RR < 1.60 * DISK_RADIUS)
FAR = RR > 1.25


class NightMoonRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/moon.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testCenter;
uniform float testNight;
uniform float testOvercast;
void main() {
    vec2 p = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 center = normalize(testCenter);
    vec3 helper = abs(center.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(center, helper));
    vec3 up = cross(right, center);
    vec3 ray = normalize(center + right * p.x * tan(radians(3.0)) +
                         up * p.y * tan(radians(3.0)));
    gl_FragColor = vec4(moonSky(ray, testNight, testOvercast), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testCenter', [0.0, 1.0, 0.0])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def sky(cls, phase, rain=0.0, night=1.0):
        """Moon at zenith; the sun is opposite. Phase 0 full, 4 new."""
        moon = np.array([0.0, 100.0, 0.0], dtype=np.float32)
        sun = -moon
        cls.renderer.uniform(cls.program, 'sunPosition', sun)
        cls.renderer.uniform(cls.program, 'moonPosition', moon)
        cls.renderer.uniform(cls.program, 'shadowLightPosition', sun)
        cls.renderer.uniform(cls.program, 'moonPhase', int(phase))
        cls.renderer.uniform(cls.program, 'testNight', float(night))
        cls.renderer.uniform(cls.program, 'testOvercast', float(rain) * 0.84)
        cls.renderer.full_screen()
        cls.renderer.check('night moon')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def brightness(image):
        return image @ np.array([0.2126, 0.7152, 0.0722], np.float32)

    def test_daylight_gate(self):
        day = self.sky(0, night=0.0)
        self.assertLess(float(day.max()), 1e-5, 'Moon must vanish in daylight')

    def test_deterministic(self):
        a = self.brightness(self.sky(0))
        b = self.brightness(self.sky(0))
        np.testing.assert_array_equal(a, b, 'Moon must be stable between frames')

    def test_full_moon_and_halo(self):
        image = self.brightness(self.sky(0))
        disk = float(image[DISK].mean())
        halo = float(image[HALO].mean())
        far = float(image[FAR].mean())
        self.assertGreater(disk, 0.5, 'Full moon disk must read as a bright body')
        self.assertGreater(halo, far * 2.0, 'Halo must fall off around the disk')
        self.assertGreater(halo, 0.006, 'Halo must remain visible, not vanish')
        self.assertLess(halo, disk * 0.35, 'Halo must stay below the disk itself')

    def test_new_moon_goes_dark(self):
        full = self.brightness(self.sky(0))
        new = self.brightness(self.sky(4))
        disk = float(new[DISK].mean())
        self.assertLess(disk, float(full[DISK].mean()) * 0.10,
                        'New moon must not show an illuminated disk')
        self.assertLess(disk, 0.06, 'Earthshine must stay faint')
        self.assertLess(float(new[HALO].mean()), float(full[HALO].mean()) * 0.85,
                        'New moon halo must be weaker than the full moon halo')

    def test_quarter_phases_mirror(self):
        waxing = self.brightness(self.sky(6))  # first quarter
        waning = self.brightness(self.sky(2))  # last quarter
        for name, image in (('phase 6', waxing), ('phase 2', waning)):
            lit = (image[QUARTER] > 0.25).mean()
            self.assertGreater(float(lit), 0.30, f'{name} must show a lit half')
            self.assertLess(float(lit), 0.70, f'{name} must stay a half moon')
        def centroid_x(image):
            weights = np.where(image > 0.25, image, 0.0)
            return float((weights * PX).sum() / max(weights.sum(), 1e-8))
        self.assertLess(centroid_x(waxing) * centroid_x(waning), 0.0,
                        'Waxing and waning crescents must mirror')
        self.assertGreater(abs(centroid_x(waxing) - centroid_x(waning)), 0.20,
                           'The lit limb must flip sides between the phases')

    def test_disk_is_bounded(self):
        image = self.brightness(self.sky(0))
        disk = float(image[DISK].mean())
        beyond = float(image[RR > 1.15 * DISK_RADIUS].max())
        self.assertLess(beyond, disk * 0.35,
                        'Nothing bright may leak beyond the moon limb')

    def test_overcast_dims_the_moon(self):
        clear = self.brightness(self.sky(0))
        rain = self.brightness(self.sky(0, rain=1.0))
        self.assertLess(float(rain[DISK].mean()), float(clear[DISK].mean()) * 0.45,
                        'Overcast weather must strongly dim the moon')


if __name__ == '__main__':
    unittest.main()
