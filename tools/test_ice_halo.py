"""GPU checks for the analytic 22-degree ice-crystal halo.

The fixture samples the authored halo function over a synthetic sky dome. It is
an engineering check, not a Minecraft screenshot or a scattering simulation.
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


class IceHaloRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/ice_halo.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testLight;
uniform float testVisibility;
uniform float testLunar;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.30;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = iceHalo(ray, normalize(testLight), testVisibility,
                         vec3(1.0), testLunar);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_elevation_deg, visibility=1.0, lunar=0.0):
        rad = np.deg2rad(sun_elevation_deg)
        cls.renderer.uniform(cls.program, 'testLight',
                             light_vector(rad).tolist())
        cls.renderer.uniform(cls.program, 'testVisibility', visibility)
        cls.renderer.uniform(cls.program, 'testLunar', lunar)
        cls.renderer.full_screen()
        cls.renderer.check('ice halo')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data, cls.rays

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    @staticmethod
    def angular(rays, sun_elevation_deg):
        light = light_vector(np.deg2rad(sun_elevation_deg))
        return np.degrees(np.arccos(np.clip(rays @ light, -1.0, 1.0)))

    @staticmethod
    def azimuths(rays):
        return np.degrees(np.arctan2(rays[:, :, 2], rays[:, :, 0]))

    def test_deterministic(self):
        a, _ = self.image(15.0)
        b, _ = self.image(15.0)
        np.testing.assert_array_equal(a, b, 'Halo must be stable')

    def test_ring_sits_at_22_degrees(self):
        image, rays = self.image(21.0)
        theta = self.angular(rays, 21.0)
        ring = self.peak(image, np.abs(theta - 22.0) < 0.7)
        inner = self.peak(image, np.abs(theta - 11.0) < 2.0)
        outer = self.peak(image, np.abs(theta - 34.0) < 2.0)
        self.assertGreater(ring, 0.02, 'The 22-degree ring must be visible')
        self.assertLess(inner, ring * 0.1, 'No false inner disc')
        self.assertLess(outer, ring * 0.1, 'No false outer disc')

    def test_visibility_suppresses_everything(self):
        image, _ = self.image(21.0, visibility=0.0)
        self.assertLess(float(image.max()), 1e-7)

    def test_sun_dogs_appear_only_with_a_low_sun(self):
        low, rays = self.image(7.0)
        high, _ = self.image(26.0)
        elevation = np.degrees(np.arcsin(np.clip(rays[:, :, 1], -1.0, 1.0)))
        azimuth = np.abs(self.azimuths(rays))
        dogs = (np.abs(elevation - 7.0) < 3.0) & (np.abs(azimuth - 22.0) < 4.0)
        low_peak = self.peak(low, dogs)
        high_peak = self.peak(high, dogs)
        self.assertGreater(low_peak, 0.14, 'Sun dogs must brighten the ring')
        self.assertGreater(low_peak, high_peak * 1.5,
                           'The low-sun gate must matter')

    def test_pillar_extends_above_a_horizon_sun(self):
        low, rays = self.image(3.5)
        high, _ = self.image(30.0)
        elevation = np.degrees(np.arcsin(np.clip(rays[:, :, 1], -1.0, 1.0)))
        azimuth = np.abs(self.azimuths(rays))

        def column_band(sun):
            return ((elevation > sun + 1.0) & (elevation < sun + 6.0) &
                    (azimuth < 2.0))

        def beside_band(sun):
            return ((elevation > sun + 1.0) & (elevation < sun + 6.0) &
                    (azimuth > 8.0) & (azimuth < 14.0))

        column_peak = self.peak(low, column_band(3.5))
        beside_peak = self.peak(low, beside_band(3.5))
        self.assertGreater(column_peak, 0.015, 'Pillar must be visible')
        self.assertGreater(column_peak, beside_peak * 4.0,
                           'Pillar stays a narrow vertical shaft')
        self.assertLess(self.peak(high, column_band(30.0)),
                        column_peak * 0.15,
                        'Pillar fades once the sun is high')

    def test_lunar_mode_keeps_the_ring_without_dogs(self):
        lunar, rays = self.image(7.0, lunar=1.0)
        solar, _ = self.image(7.0, lunar=0.0)
        theta = self.angular(rays, 7.0)
        ring = self.peak(lunar, np.abs(theta - 22.0) < 0.7)
        self.assertGreater(ring, 0.02, 'Moonlight draws the same 22-degree ring')
        elevation = np.degrees(np.arcsin(np.clip(rays[:, :, 1], -1.0, 1.0)))
        azimuth = np.abs(self.azimuths(rays))
        dogs = (np.abs(elevation - 7.0) < 3.0) & (np.abs(azimuth - 22.0) < 4.0)
        self.assertLess(self.peak(lunar, dogs), self.peak(solar, dogs) * 0.6,
                        'Lunar mode must not add sun dogs')


if __name__ == '__main__':
    unittest.main()
