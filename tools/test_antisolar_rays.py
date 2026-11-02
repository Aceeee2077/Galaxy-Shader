"""GPU checks for the analytic anti-solar (anticrepuscular) ray fan.

The fixture samples the authored function over an equirectangular strip of the
sky, with one variant aimed at the sunward half. It is an engineering check, not
a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 160
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
SUN_LOW = (np.cos(0.02), np.sin(0.02), 0.0)


class AntisolarRaysRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/antisolar_rays.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testOvercast;
uniform float testFlip;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-90.0 + 180.0 * uv.x) + testFlip * PI;
    float el = radians(-30.0 + 90.0 * uv.y);
    vec3 sun = normalize(testSun);
    vec3 anti = -sun;
    vec3 forward = normalize(vec3(anti.x, 0.0, anti.z));
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 ray = normalize(forward * cos(az) * cos(el) +
                         right * sin(az) * cos(el) +
                         vec3(0.0, 1.0, 0.0) * sin(el));
    gl_FragColor = vec4(anticrepuscularRays(ray, sun, testOvercast), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])

        u = (np.arange(W) + 0.5) / W
        v = (np.arange(H) + 0.5) / H
        az = np.deg2rad(-90.0 + 180.0 * u)
        el = np.deg2rad(-30.0 + 90.0 * v)
        cls.el = np.broadcast_to(el[:, None], (H, W))
        cls.az = np.broadcast_to(az[None, :], (H, W))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun=SUN_LOW, overcast=0.0, flip=0.0):
        cls.renderer.uniform(cls.program, 'testSun', list(sun))
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'testFlip', flip)
        cls.renderer.full_screen()
        cls.renderer.check('anti-solar rays')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def distance_map(self, sun=SUN_LOW, flip=0.0):
        sun = np.asarray(sun, dtype=float)
        anti = -sun
        forward = np.array([anti[0], 0.0, anti[2]])
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, np.array([0.0, 1.0, 0.0]))
        right /= np.linalg.norm(right)
        az = self.az + flip * np.pi
        ray = (forward[None, None, :] * np.cos(az)[:, :, None] *
               np.cos(self.el)[:, :, None] +
               right[None, None, :] * np.sin(az)[:, :, None] *
               np.cos(self.el)[:, :, None] +
               np.array([0.0, 1.0, 0.0])[None, None, :] * np.sin(self.el)[:, :, None])
        ray /= np.linalg.norm(ray, axis=2, keepdims=True)
        return np.arccos(np.clip(ray @ anti, -1.0, 1.0)), ray

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Anti-solar rays must be stable')

    def test_visible_only_away_from_the_antisolar_point(self):
        image = self.image()
        distance, _ = self.distance_map()
        core = float(image[(distance < 0.035)].max())
        fan = float(image[(distance > 0.20) & (self.el > 0.03)].max())
        self.assertLess(core, 1e-7, 'The fan must not glow at its own focus')
        self.assertGreater(fan, 1e-3, 'The fan must be visible around the focus')

    def test_no_rays_in_the_sunward_half(self):
        image = self.image(flip=1.0)
        self.assertEqual(float(image.max()), 0.0,
                         'Anti-solar rays only belong opposite the sun')

    def test_high_sun_and_deep_night_gate(self):
        high = (np.cos(0.30), np.sin(0.30), 0.0)
        night = (np.cos(-0.25), np.sin(-0.25), 0.0)
        self.assertEqual(float(self.image(sun=high).max()), 0.0)
        self.assertEqual(float(self.image(sun=night).max()), 0.0)

    def test_overcast_dims_the_fan(self):
        clear = float(self.image(overcast=0.0).mean())
        cloudy = float(self.image(overcast=0.9).mean())
        self.assertGreater(clear, 0.0)
        self.assertLess(cloudy, clear * 0.55)

    def test_azimuthal_spokes(self):
        lum = self.image().mean(axis=2)
        rows = np.where((self.el[:, 0] > 0.12) & (self.el[:, 0] < 0.35))[0]
        profile = lum[rows, :].max(axis=0)  # brightness per azimuth
        active = profile[profile > 0.0]
        self.assertGreater(active.size, 32, 'The fan must span many headings')
        self.assertGreater(profile.max(), float(active.mean()) * 1.6,
                           'Bright and dark spokes must alternate')
        self.assertGreater(float(active.std()), float(active.mean()) * 0.30,
                           'The spokes need real contrast')

    def test_below_horizon_stays_dark(self):
        image = self.image()
        below = image[self.el < np.deg2rad(-2.0)]
        self.assertEqual(float(below.max()), 0.0)
        above = image[self.el > np.deg2rad(5.0)]
        self.assertGreater(float(above.max()), 1e-3)


if __name__ == '__main__':
    unittest.main()
