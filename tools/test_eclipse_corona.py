"""GPU checks for the solar eclipse corona.

The fixture samples the authored corona in a polar grid around the Sun. It is
an engineering check, not a Minecraft screenshot or a magnetohydrodynamic model.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 720, 200
MAX_RADIUS = 0.35
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
SUN = np.array([np.cos(0.61), np.sin(0.61), 0.0])
SUN = SUN / np.linalg.norm(SUN)


def polar_grid():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    az = u * 2.0 * np.pi
    r = v * MAX_RADIUS
    ref = np.array([0.0, 1.0, 0.0]) if abs(SUN[1]) < 0.95 else np.array([1.0, 0.0, 0.0])
    east = np.cross(ref, SUN)
    east /= np.linalg.norm(east)
    north = np.cross(SUN, east)
    rays = (SUN[None, None, :] * np.cos(r)[:, None, None] +
            east[None, None, :] * (np.sin(r)[:, None] * np.cos(az)[None, :])[:, :, None] +
            north[None, None, :] * (np.sin(r)[:, None] * np.sin(az)[None, :])[:, :, None])
    return rays / np.linalg.norm(rays, axis=-1, keepdims=True)


class EclipseCoronaRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/eclipse_corona.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testEclipse;
uniform float testTime;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 sun = normalize(testSun);
    vec3 ref = abs(sun.y) < 0.95 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 east = normalize(cross(ref, sun));
    vec3 north = cross(sun, east);
    float az = uv.x * 6.2831853;
    float r = uv.y * 0.35;
    vec3 ray = normalize(sun * cos(r) + east * sin(r) * cos(az) +
                         north * sin(r) * sin(az));
    gl_FragColor = vec4(eclipseCorona(ray, sun, testEclipse, testTime), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testSun', SUN.tolist())
        cls.rays = polar_grid()
        cls.radius = np.degrees(np.arccos(np.clip(cls.rays @ SUN, -1.0, 1.0)))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, eclipse=1.0, time=0.0):
        cls.renderer.uniform(cls.program, 'testEclipse', eclipse)
        cls.renderer.uniform(cls.program, 'testTime', time)
        cls.renderer.full_screen()
        cls.renderer.check('eclipse corona')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'The corona must be stable')

    def test_corona_is_confined_to_the_sun(self):
        image = self.image()
        near = (self.radius > 2.0) & (self.radius < 8.0)
        far = self.radius > 18.0
        self.assertGreater(float(image[near].max()), 0.01,
                           'The corona must glow around the disk')
        self.assertLess(float(image[far].max()), 1e-7,
                        'Nothing far from the Sun')

    def test_radial_falloff(self):
        image = self.image().mean(axis=2)
        inner = (self.radius > 2.0) & (self.radius < 4.0)
        outer = (self.radius > 8.0) & (self.radius < 12.0)
        self.assertGreater(float(image[inner].max()),
                           float(image[outer].max()) * 1.5,
                           'Corona brightness falls with radius')

    def test_streamers_alternate_around_the_disk(self):
        image = self.image().mean(axis=2)
        row = int((5.5 * np.pi / 180.0) / MAX_RADIUS * H)
        prof = image[row]
        self.assertGreater(float(prof.std()), float(prof.mean()) * 0.08,
                           'Streamers must vary around the limb')
        smooth = np.convolve(prof, np.ones(5) / 5.0, mode='valid')
        peaks = np.sum((smooth[1:-1] >= smooth[:-2]) &
                       (smooth[1:-1] > smooth[2:]))
        self.assertGreaterEqual(int(peaks), 4,
                               'Several radial streamers must survive')

    def test_prominences_are_red_on_the_limb(self):
        image = self.image()
        limb = (self.radius > 0.55) & (self.radius < 0.80)
        red = float(image[limb][:, 0].max())
        blue = float(image[limb][:, 2].max())
        self.assertGreater(red, 0.01, 'Prominences must be visible')
        self.assertGreater(red, blue * 1.3,
                           'Prominences are red, not white streamers')

    def test_eclipse_gate_and_linear_scaling(self):
        self.assertEqual(float(self.image(eclipse=0.0).max()), 0.0)
        half = float(self.image(eclipse=0.5).max())
        full = float(self.image(eclipse=1.0).max())
        self.assertGreater(half, full * 0.3)
        self.assertLess(half, full * 0.6)


if __name__ == '__main__':
    unittest.main()
