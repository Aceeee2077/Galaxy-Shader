"""GPU checks for the supernumerary interference arcs.

The fixture samples the authored function over a synthetic sky dome. It is an
engineering check, not a Minecraft screenshot or a rigorous Mie calculation.
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


class SupernumeraryRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/supernumerary.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testMoisture;
uniform float testOvercast;
uniform float testDay;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.00;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(supernumeraryArcs(ray, normalize(testSun),
                                          testMoisture, testOvercast, testDay), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.sun = np.array([-np.cos(np.deg2rad(25.0)),
                            np.sin(np.deg2rad(25.0)), 0.0])
        cls.angle = np.arccos(np.clip(cls.rays @ (-cls.sun), -1.0, 1.0))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, moisture=1.0, overcast=0.0, day=1.0, sun_elevation=25.0):
        sun = np.array([-np.cos(np.deg2rad(sun_elevation)),
                        np.sin(np.deg2rad(sun_elevation)), 0.0])
        cls.renderer.uniform(cls.program, 'testSun', sun.tolist())
        cls.renderer.uniform(cls.program, 'testMoisture', moisture)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'testDay', day)
        cls.renderer.full_screen()
        cls.renderer.check('supernumerary arcs')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Supernumeraries must be stable')

    def test_band_sits_inside_the_primary(self):
        image = self.image()
        band = self.peak(image, (self.angle > np.deg2rad(36.0)) &
                         (self.angle < np.deg2rad(40.0)))
        inner = self.peak(image, (self.angle > np.deg2rad(30.0)) &
                          (self.angle < np.deg2rad(34.0)))
        outside = self.peak(image, (self.angle > np.deg2rad(43.0)) &
                            (self.angle < np.deg2rad(47.0)))
        self.assertGreater(band, 0.005, 'Arcs must be visible inside the bow')
        self.assertLess(inner, 1e-7, 'Nothing well inside the bow')
        self.assertLess(outside, 1e-7, 'Nothing outside the primary')

    def test_fringes_alternate_radially(self):
        image = self.image().mean(axis=2)
        ramp = np.linspace(np.deg2rad(35.5), np.deg2rad(40.0), 46)
        profile = np.array([
            image[np.abs(self.angle - a) < np.deg2rad(0.06)].mean()
            for a in ramp])
        active = profile[profile > 1e-6]
        self.assertGreater(active.size, 20)
        self.assertGreater(float(active.std()), float(active.mean()) * 0.12,
                           'Fringes must modulate the band')
        peaks = np.sum((profile[1:-1] > profile[:-2]) &
                       (profile[1:-1] > profile[2:]) &
                       (profile[1:-1] > float(profile.max()) * 0.10))
        self.assertGreaterEqual(int(peaks), 3, 'Several fringes must resolve')

    def test_moisture_gate(self):
        self.assertEqual(float(self.image(moisture=0.0).max()), 0.0)

    def test_day_and_sun_gates(self):
        self.assertEqual(float(self.image(day=0.0).max()), 0.0)
        self.assertEqual(float(self.image(sun_elevation=-2.0).max()), 0.0)

    def test_overcast_dims_the_arcs(self):
        clear = float(self.image(overcast=0.0).max())
        cloudy = float(self.image(overcast=0.9).max())
        self.assertGreater(clear, cloudy * 2.0)


if __name__ == '__main__':
    unittest.main()
