"""GPU checks for the upper Parry arc in the ice-crystal companion family.

The fixture samples the authored ice-halo companion function over a synthetic
sky dome. It is an engineering check, not a Minecraft screenshot or a
scattering simulation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 120
MAX_ELEVATION = 1.30
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


def light_vector(elevation):
    return np.array([np.cos(elevation), np.sin(elevation), 0.0])


class ParryArcRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/ice_halo_extras.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.30;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = iceHaloCompanions(ray, normalize(testSun), testVisibility);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.elevation = np.arcsin(np.clip(cls.rays[:, :, 1], -1.0, 1.0))
        cls.azimuth = np.arctan2(cls.rays[:, :, 2], cls.rays[:, :, 0])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_elevation_deg, visibility=1.0):
        rad = np.deg2rad(sun_elevation_deg)
        cls.renderer.uniform(cls.program, 'testSun',
                             light_vector(rad).tolist())
        cls.renderer.uniform(cls.program, 'testVisibility', visibility)
        cls.renderer.full_screen()
        cls.renderer.check('parry arc')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def bow_mask(elevation, azimuth, sun_elevation_deg):
        sun = np.deg2rad(sun_elevation_deg)
        return ((np.abs(azimuth) < np.deg2rad(15.0)) &
                (np.abs(elevation - sun - np.deg2rad(25.0)) < np.deg2rad(2.0)))

    def test_visible_for_low_sun(self):
        image = self.image(24.0)
        mask = self.bow_mask(self.elevation, self.azimuth, 24.0)
        self.assertTrue(mask.any())
        self.assertGreater(float(image[mask].max()), 1.0e-3)

    def test_gone_before_sunrise(self):
        image = self.image(0.0)
        mask = self.bow_mask(self.elevation, self.azimuth, 0.0)
        self.assertTrue(mask.any())
        self.assertLess(float(image[mask].max()), 1.0e-6)

    def test_gone_above_high_sun_cutoff(self):
        image = self.image(45.0)
        mask = self.bow_mask(self.elevation, self.azimuth, 45.0)
        self.assertTrue(mask.any())
        self.assertLess(float(image[mask].max()), 1.0e-6)

    def test_narrow_vertical_band(self):
        image = self.image(24.0)
        mask = self.bow_mask(self.elevation, self.azimuth, 24.0)
        peak = float(image[mask].max())
        sun = np.deg2rad(24.0)
        off = ((np.abs(self.azimuth) < np.deg2rad(5.0)) &
               (np.abs(self.elevation - sun - np.deg2rad(29.0)) < np.deg2rad(1.0)))
        self.assertTrue(off.any())
        self.assertLess(float(image[off].max()), peak * 0.5)

    def test_zero_visibility_is_black(self):
        image = self.image(24.0, visibility=0.0)
        self.assertEqual(float(image.max()), 0.0)

    def test_deterministic(self):
        a = self.image(24.0)
        b = self.image(24.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
