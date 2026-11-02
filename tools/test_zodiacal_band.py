"""GPU checks for the analytic night-time zodiacal band and gegenschein.

The fixture samples the authored sky function over a synthetic dome. It is an
engineering check, not a Minecraft screenshot or a dust-cloud simulation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 120
MAX_ELEVATION = 1.20
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


def sun_vector(elevation):
    # The sun sets behind the observer; the anti-solar point (and gegenschein)
    # is in the middle of the panorama.
    return np.array([-np.cos(elevation), np.sin(elevation), 0.0])


class ZodiacalBandRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/zodiacal_band.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.20;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(zodiacalBand(ray, normalize(testSun), testOvercast), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.sun = sun_vector(-0.55)
        cls.normal = np.cross([0.0, 0.0, 1.0], cls.sun)
        cls.normal /= np.linalg.norm(cls.normal)
        cls.latitude = cls.rays @ cls.normal
        cls.anti = -cls.sun
        cls.anti_angle = np.degrees(
            np.arccos(np.clip(cls.rays @ cls.anti, -1.0, 1.0)))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_elevation=-0.55, overcast=0.0):
        cls.renderer.uniform(cls.program, 'testSun',
                             sun_vector(sun_elevation).tolist())
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.full_screen()
        cls.renderer.check('zodiacal band')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'The band must be stable')

    def test_band_follows_the_ecliptic(self):
        image = self.image()
        on = self.peak(image, (np.abs(self.latitude) < np.deg2rad(0.5)) &
                        (self.rays[:, :, 1] > 0.05))
        off = self.peak(image, (np.abs(self.latitude) > np.deg2rad(20.0)) &
                        (self.rays[:, :, 1] > 0.05))
        self.assertGreater(on, 0.005, 'The ecliptic band must be visible')
        self.assertLess(off, 1e-7, 'No light far from the ecliptic')

    def test_day_and_twilight_gate(self):
        self.assertLess(float(self.image(0.30).max()), 1e-7)
        self.assertLess(float(self.image(-0.10).max()), 1e-7)
        self.assertGreater(float(self.image(-0.55).max()), 0.02)

    def test_gegenschein_is_the_brightest_part(self):
        image = self.image()
        spot = self.peak(image, self.anti_angle < 3.0)
        band = self.peak(image, (np.abs(self.latitude) < np.deg2rad(0.5)) &
                         (self.anti_angle > 80.0) & (self.anti_angle < 100.0) &
                         (self.rays[:, :, 1] > 0.05))
        self.assertGreater(spot, 0.025)
        self.assertGreater(spot, band * 1.5,
                           'The anti-solar oval must stand above the band')

    def test_overcast_removes_the_band(self):
        clear = self.image(overcast=0.0)
        cloudy = self.image(overcast=1.0)
        self.assertGreater(float(clear.max()), 0.02)
        self.assertLess(float(cloudy.max()), 1e-7)

    def test_gegenschein_is_warmer_than_the_band(self):
        image = self.image()
        spot = image[(self.anti_angle < 2.0) & (self.rays[:, :, 1] > 0.2)]
        band = image[(np.abs(self.latitude) < np.deg2rad(0.5)) &
                     (self.anti_angle > 80.0) & (self.anti_angle < 100.0) &
                     (self.rays[:, :, 1] > 0.05)]
        spot_rgb = spot.mean(axis=0)
        band_rgb = band.mean(axis=0)
        self.assertGreater(spot_rgb[0], spot_rgb[2] * 1.02,
                           'The anti-solar oval reads warm silver')
        self.assertGreater(band_rgb[2], band_rgb[0] * 1.15,
                           'The outer band reads cool silver-blue')


if __name__ == '__main__':
    unittest.main()
