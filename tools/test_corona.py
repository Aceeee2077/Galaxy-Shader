"""GPU checks for the lunar corona.

The fixture samples the authored function over a synthetic night dome. It is an
engineering check, not a Minecraft screenshot or a rigorous diffraction model.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 160
MAX_ELEVATION = 1.00
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def ray_grid():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    azimuth = (u * 2.0 - 1.0) * np.pi
    elevation = v * MAX_ELEVATION
    cos_e = np.cos(elevation)[:, None]
    return np.stack([cos_e * np.cos(azimuth)[None, :],
                     np.sin(elevation)[:, None] * np.ones_like(u)[None, :],
                     cos_e * np.sin(azimuth)[None, :]], axis=-1)


class CoronaRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/corona.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testMoon;
uniform float testLit;
uniform float testOvercast;
uniform float testNight;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.00;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(lunarCorona(ray, normalize(testMoon), testLit,
                                    testOvercast, testNight), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.moon = np.array([np.cos(np.deg2rad(25.0)),
                             np.sin(np.deg2rad(25.0)), 0.0])
        cls.angle = np.arccos(np.clip(cls.rays @ cls.moon, -1.0, 1.0))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, lit=1.0, overcast=0.0, night=1.0, moon_elevation=25.0):
        moon = np.array([np.cos(np.deg2rad(moon_elevation)),
                         np.sin(np.deg2rad(moon_elevation)), 0.0])
        cls.renderer.uniform(cls.program, 'testMoon', moon.tolist())
        cls.renderer.uniform(cls.program, 'testLit', lit)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'testNight', night)
        cls.renderer.full_screen()
        cls.renderer.check('lunar corona')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Corona must be stable')

    def test_rings_stay_compact_around_the_moon(self):
        image = self.image()
        near = self.peak(image, (self.angle > np.deg2rad(2.0)) &
                         (self.angle < np.deg2rad(8.0)))
        far = self.peak(image, self.angle > np.deg2rad(14.0))
        self.assertGreater(near, 0.01, 'Corona must be visible near the moon')
        self.assertLess(far, 1e-7, 'Nothing beyond the outer envelope')

    def test_rings_alternate_radially(self):
        image = self.image().mean(axis=2)
        ramp = np.linspace(np.deg2rad(2.0), np.deg2rad(8.0), 46)
        profile = np.array([
            image[np.abs(self.angle - a) < np.deg2rad(0.08)].mean()
            for a in ramp])
        active = profile[profile > 1e-7]
        self.assertGreater(active.size, 20)
        self.assertGreater(float(active.std()), float(active.mean()) * 0.15,
                           'Rings must modulate the glow')
        peaks = np.sum((profile[1:-1] > profile[:-2]) &
                       (profile[1:-1] > profile[2:]) &
                       (profile[1:-1] > float(profile.max()) * 0.10))
        self.assertGreaterEqual(int(peaks), 2, 'Several rings must resolve')

    def test_rainbow_ordering_of_the_tints(self):
        image = self.image()
        inner = image[(self.angle > np.deg2rad(2.8)) &
                      (self.angle < np.deg2rad(3.4))].mean(axis=0)
        outer = image[(self.angle > np.deg2rad(6.8)) &
                      (self.angle < np.deg2rad(7.4))].mean(axis=0)
        self.assertGreater(inner[2], inner[0],
                           'Inner ring must lean blue')
        self.assertGreater(outer[0], outer[2],
                           'Outer ring must lean warm')

    def test_phase_and_night_gates(self):
        self.assertEqual(float(self.image(lit=0.0).max()), 0.0)
        self.assertEqual(float(self.image(night=0.0).max()), 0.0)
        below = float(self.image(moon_elevation=-12.0).max())
        self.assertEqual(below, 0.0, 'No corona for a set moon')

    def test_thin_cloud_and_overcast(self):
        clear = float(self.image(overcast=0.0).max())
        cloudy = float(self.image(overcast=0.9).max())
        self.assertGreater(clear, cloudy * 2.5)


if __name__ == '__main__':
    unittest.main()
