"""GPU checks for the auroral zenith corona.

The fixture samples the authored function over the upper sky dome. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 160
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def ray_grid():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    azimuth = (u * 2.0 - 1.0) * np.pi
    elevation = np.arcsin(0.45 + 0.55 * v)  # 26.7 to 90 degrees
    cos_e = np.cos(elevation)[:, None]
    return np.stack([cos_e * np.cos(azimuth)[None, :],
                     np.sin(elevation)[:, None] * np.ones_like(u)[None, :],
                     cos_e * np.sin(azimuth)[None, :]], axis=-1)


class AuroraCoronaRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/aurora_corona.glsl') +
                    '''
uniform vec2 testResolution;
uniform float testStrength;
uniform float testTime;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = asin(0.45 + 0.55 * uv.y);
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(auroraCorona(ray, testStrength, testTime), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.elevation = np.arcsin(cls.rays[:, :, 1])
        cls.azimuth = np.arctan2(cls.rays[:, :, 2], cls.rays[:, :, 0])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, strength=1.0, time=7.0):
        cls.renderer.uniform(cls.program, 'testStrength', strength)
        cls.renderer.uniform(cls.program, 'testTime', time)
        cls.renderer.full_screen()
        cls.renderer.check('aurora corona')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Aurora corona must be stable')

    def test_corona_is_capped_to_the_zenith(self):
        image = self.image()
        high = float(image[self.elevation > np.deg2rad(65.0)].max())
        low = float(image[self.elevation < np.deg2rad(30.0)].max())
        self.assertGreater(high, 0.01, 'The corona must brighten overhead')
        self.assertEqual(low, 0.0, 'It must not reach the lower sky')

    def test_rays_converge_with_azimuth_structure(self):
        image = self.image().mean(axis=2)
        row = (self.elevation > np.deg2rad(70.0)) & (self.elevation < np.deg2rad(80.0))
        profile = image[row]
        active = profile[profile > 1e-6]
        self.assertGreater(active.size, 20)
        self.assertGreater(float(active.std()), float(active.mean()) * 0.25,
                           'The cap must be split into rays')
        peaks = np.sum((profile[1:-1] > profile[:-2]) &
                       (profile[1:-1] > profile[2:]) &
                       (profile[1:-1] > float(profile.max()) * 0.10))
        self.assertGreaterEqual(int(peaks), 3)

    def test_brightness_falls_away_from_the_zenith(self):
        image = self.image().mean(axis=2)
        centre = image[self.elevation > np.deg2rad(80.0)].mean()
        edge = image[self.elevation < np.deg2rad(55.0)].mean()
        self.assertGreater(float(centre), float(edge) * 4.0)

    def test_green_core_and_violet_fringe(self):
        image = self.image()
        centre = image[self.elevation > np.deg2rad(78.0)].mean(axis=0)
        fringe = image[(self.elevation > np.deg2rad(55.0)) &
                       (self.elevation < np.deg2rad(60.0))].mean(axis=0)
        self.assertGreater(centre[1], centre[0] * 1.5)
        self.assertGreater(fringe[2] + fringe[0], fringe[1] * 1.2)

    def test_strength_gate(self):
        self.assertEqual(float(self.image(strength=0.0).max()), 0.0)


if __name__ == '__main__':
    unittest.main()
