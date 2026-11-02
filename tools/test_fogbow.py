"""GPU checks for the fog bow.

The fixture samples the authored function over a synthetic sky dome facing the
anti-solar point. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 160
MAX_ELEVATION = 1.10
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


class FogbowRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/fogbow.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testFog;
uniform float testDay;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.10;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(fogbow(ray, normalize(testSun), testFog, testDay), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.sun = np.array([-np.cos(np.deg2rad(20.0)),
                            np.sin(np.deg2rad(20.0)), 0.0])
        cls.angle = np.arccos(np.clip(cls.rays @ (-cls.sun), -1.0, 1.0))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, fog=1.0, day=1.0, sun_elevation=20.0):
        sun = np.array([-np.cos(np.deg2rad(sun_elevation)),
                        np.sin(np.deg2rad(sun_elevation)), 0.0])
        cls.renderer.uniform(cls.program, 'testSun', sun.tolist())
        cls.renderer.uniform(cls.program, 'testFog', fog)
        cls.renderer.uniform(cls.program, 'testDay', day)
        cls.renderer.full_screen()
        cls.renderer.check('fog bow')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'The fog bow must be stable')

    def test_bow_sits_at_forty_two_degrees(self):
        image = self.image()
        bow = self.peak(image, (self.angle > np.deg2rad(40.0)) &
                        (self.angle < np.deg2rad(45.0)))
        inner = self.peak(image, (self.angle > np.deg2rad(30.0)) &
                          (self.angle < np.deg2rad(35.0)))
        outer = self.peak(image, (self.angle > np.deg2rad(50.0)) &
                          (self.angle < np.deg2rad(55.0)))
        self.assertGreater(bow, 0.01, 'The broad fog bow must be visible')
        self.assertLess(inner, 1e-7, 'Nothing well inside the bow')
        self.assertLess(outer, 1e-7, 'Nothing outside the bow')

    def test_bow_is_almost_white(self):
        image = self.image()
        bow = image[(self.angle > np.deg2rad(41.0)) &
                    (self.angle < np.deg2rad(44.0))]
        mean = bow.mean(axis=0)
        self.assertLess(float(mean.max() / mean.min()), 1.35,
                        'Fog droplets smear the spectrum into white')
        inner = image[(self.angle > np.deg2rad(39.8)) &
                      (self.angle < np.deg2rad(40.8))].mean(axis=0)
        outer = image[(self.angle > np.deg2rad(45.0)) &
                      (self.angle < np.deg2rad(46.0))].mean(axis=0)
        self.assertGreater(inner[2], inner[0], 'Inner rim leans cool')
        self.assertGreater(outer[0], outer[2], 'Outer rim leans warm')

    def test_fog_and_day_gate(self):
        self.assertEqual(float(self.image(fog=0.0).max()), 0.0)
        self.assertEqual(float(self.image(day=0.0).max()), 0.0)

    def test_sun_must_be_low_and_above_the_horizon(self):
        self.assertEqual(float(self.image(sun_elevation=-2.0).max()), 0.0)
        high = float(self.image(sun_elevation=60.0).max())
        self.assertEqual(high, 0.0, 'A high sun pushes the bow underground')

    def test_fog_strength_scales_the_bow(self):
        thin = float(self.image(fog=0.25).max())
        thick = float(self.image(fog=1.0).max())
        self.assertGreater(thick, thin * 3.0)


if __name__ == '__main__':
    unittest.main()
