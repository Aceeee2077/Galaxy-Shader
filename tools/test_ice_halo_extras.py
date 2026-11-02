"""GPU checks for the 46-degree halo, CHA and circumzenithal arc.

The fixture samples the authored companion-halo function over an
equirectangular sky grid facing the sun's azimuth. It is an engineering check,
not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 180
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
RING = np.deg2rad(46.0)


class IceHaloExtrasRegression(unittest.TestCase):
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
    float az = radians(-90.0 + 180.0 * uv.x);
    float el = radians(-5.0 + 85.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(iceHaloCompanions(ray, normalize(testSun),
                                          testVisibility), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])

        u = (np.arange(W) + 0.5) / W
        v = (np.arange(H) + 0.5) / H
        cls.az = np.broadcast_to(np.deg2rad(-90.0 + 180.0 * u)[None, :], (H, W))
        cls.el = np.broadcast_to(np.deg2rad(-5.0 + 85.0 * v)[:, None], (H, W))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_elevation, visibility=1.0):
        cls.renderer.uniform(cls.program, 'testSun',
                             [np.cos(sun_elevation), np.sin(sun_elevation), 0.0])
        cls.renderer.uniform(cls.program, 'testVisibility', visibility)
        cls.renderer.full_screen()
        cls.renderer.check('ice halo companions')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def angle_from_sun(self, sun_elevation):
        sun = np.array([np.cos(sun_elevation), np.sin(sun_elevation), 0.0])
        ray = np.stack([
            np.cos(self.el) * np.cos(self.az),
            np.sin(self.el),
            np.cos(self.el) * np.sin(self.az),
        ], axis=2)
        return np.arccos(np.clip(ray @ sun, -1.0, 1.0)), ray

    def away_from_parhelic_band(self, sun):
        return np.abs(self.el - sun) > np.deg2rad(2.5)

    def test_deterministic(self):
        a = self.image(0.524)
        b = self.image(0.524)
        np.testing.assert_array_equal(a, b, 'Companion halos must be stable')

    def test_ring_sits_at_46_degrees(self):
        angle, _ = self.angle_from_sun(0.524)
        image = self.image(0.524)
        clean = self.away_from_parhelic_band(0.524)
        ring = float(image[(np.abs(angle - RING) < np.deg2rad(1.5)) & clean].max())
        inner = float(image[(np.abs(angle - np.deg2rad(22.0)) < np.deg2rad(1.5)) & clean].max())
        outer = float(image[(np.abs(angle - np.deg2rad(65.0)) < np.deg2rad(1.5)) & clean].max())
        self.assertGreater(ring, 0.01, 'The 46-degree ring must be drawn')
        self.assertLess(inner, 1e-6, 'The 22-degree halo lives elsewhere')
        self.assertLess(outer, 1e-6, 'No ring outside 46 degrees')

    def test_ring_colour_runs_red_to_blue(self):
        angle, _ = self.angle_from_sun(0.524)
        image = self.image(0.524)
        clean = self.away_from_parhelic_band(0.524)
        inner = image[(angle > np.deg2rad(44.9)) & (angle < np.deg2rad(45.7)) & clean]
        outer = image[(angle > np.deg2rad(46.4)) & (angle < np.deg2rad(47.2)) & clean]
        red_in, blue_in = inner[:, 0].mean(), inner[:, 2].mean()
        red_out, blue_out = outer[:, 0].mean(), outer[:, 2].mean()
        self.assertGreater(red_in, blue_in * 1.25, 'Inner edge must be red')
        self.assertGreater(blue_out, red_out * 1.25, 'Outer edge must be blue')

    def test_circumhorizontal_arc_needs_high_sun(self):
        sun = 1.309  # 75 degrees
        target = np.arcsin(np.sin(sun)) - RING
        band = ((np.abs(self.el - target) < np.deg2rad(2.0)) &
                (np.abs(self.az) < np.deg2rad(30.0)))
        high = float(self.image(sun)[band].max())
        low = float(self.image(0.524)[band & self.away_from_parhelic_band(0.524)].max())
        self.assertGreater(high, 0.05, 'A high sun must light the arc')
        self.assertLess(low, 0.01, 'A 30-degree sun leaves the arc dark')

    def test_circumhorizontal_arc_is_horizontal(self):
        sun = 1.309
        target = np.arcsin(np.sin(sun)) - RING
        image = self.image(sun)
        centre = ((np.abs(self.el - target) < np.deg2rad(2.0)) &
                  (np.abs(self.az) < np.deg2rad(25.0)))
        above = ((np.abs(self.el - target - np.deg2rad(10.0)) < np.deg2rad(1.5)) &
                 (np.abs(self.az) < np.deg2rad(25.0)))
        below = ((np.abs(self.el - target + np.deg2rad(10.0)) < np.deg2rad(1.5)) &
                 (np.abs(self.az) < np.deg2rad(25.0)))
        self.assertGreater(float(image[centre].max()), 0.05)
        self.assertLess(float(image[above].max()), 1e-6, 'No arc above the band')
        self.assertLess(float(image[below].max()), 1e-6, 'No arc below the band')

    def test_circumzenithal_arc_needs_low_sun(self):
        low_sun = 0.262  # 15 degrees
        high_sun = 0.524  # 30 degrees
        target = np.arcsin(np.sin(low_sun)) + RING
        band = ((np.abs(self.el - target) < np.deg2rad(2.0)) &
                (np.abs(self.az) < np.deg2rad(25.0)))
        low = float(self.image(low_sun)[band].max())
        high = float(self.image(high_sun)[band].max())
        self.assertGreater(low, 0.05, 'A low sun must draw the high arc')
        self.assertGreater(low, high * 2.0, 'The arc must fade out by 30 degrees')

    def test_circumzenithal_arc_is_a_sunward_smile(self):
        sun = 0.262
        target = np.arcsin(np.sin(sun)) + RING
        image = self.image(sun)
        centre = ((np.abs(self.el - target) < np.deg2rad(1.5)) &
                  (np.abs(self.az) < np.deg2rad(20.0)))
        above = ((np.abs(self.el - target - np.deg2rad(8.0)) < np.deg2rad(1.5)) &
                 (np.abs(self.az) < np.deg2rad(20.0)))
        below = ((np.abs(self.el - target + np.deg2rad(8.0)) < np.deg2rad(1.5)) &
                 (np.abs(self.az) < np.deg2rad(20.0)))
        ends = ((np.abs(self.el - target) < np.deg2rad(1.5)) &
                (np.abs(self.az) > np.deg2rad(70.0)))
        self.assertGreater(float(image[centre].max()), 0.05)
        self.assertLess(float(image[above].max()), 1e-6, 'No arc above the band')
        self.assertLess(float(image[below].max()), 1e-6, 'No arc below the band')
        self.assertLess(float(image[ends].max()), 1e-6, 'The smile must end')
        lower = image[centre & (self.el < target - np.deg2rad(0.3))]
        upper = image[centre & (self.el > target + np.deg2rad(0.3))]
        self.assertGreater(lower[:, 0].mean(), lower[:, 2].mean() * 1.15,
                           'Lower edge must lean red')
        self.assertGreater(upper[:, 2].mean(), upper[:, 0].mean() * 1.15,
                           'Upper edge must lean violet')

    def test_parhelic_circle_tracks_the_sun(self):
        sun = 0.30
        image = self.image(sun)
        band = ((np.abs(self.el - sun) < np.deg2rad(0.7)) &
                (np.abs(self.az) < np.deg2rad(30.0)))
        above = ((np.abs(self.el - sun - np.deg2rad(5.0)) < np.deg2rad(1.0)) &
                 (np.abs(self.az) < np.deg2rad(30.0)))
        below = ((np.abs(self.el - sun + np.deg2rad(5.0)) < np.deg2rad(1.0)) &
                 (np.abs(self.az) < np.deg2rad(30.0)))
        self.assertGreater(float(image[band].max()), 0.005)
        self.assertLess(float(image[above].max()), 1e-6)
        self.assertLess(float(image[below].max()), 1e-6)

    def test_parhelic_circle_brightens_toward_the_sun(self):
        image = self.image(0.30)
        row = np.abs(self.el - 0.30) < np.deg2rad(0.7)
        centre = image[row & (np.abs(self.az) < np.deg2rad(10.0))]
        flank = image[row & (np.abs(self.az) > np.deg2rad(75.0))]
        self.assertGreater(centre.max(), float(flank.max()) * 1.8)

    def test_visibility_gate(self):
        self.assertEqual(float(self.image(1.309, visibility=0.0).max()), 0.0)

    def test_below_horizon_stays_dark(self):
        image = self.image(0.524)
        self.assertEqual(float(image[self.el < 0.0].max()), 0.0)
        self.assertGreater(float(image[self.el > 0.0].max()), 0.01)


if __name__ == '__main__':
    unittest.main()
