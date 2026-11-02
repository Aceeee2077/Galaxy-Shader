"""GPU checks for the analytic secondary rainbow.

The fixture samples the authored function over a synthetic sky dome. It is an
engineering check, not a Minecraft screenshot or a Mie scattering model.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 120
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


class SecondaryRainbowRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/secondary_rainbow.glsl') +
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
    gl_FragColor = vec4(secondaryRainbow(ray, normalize(testSun),
                                         testMoisture, testOvercast, testDay), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        # Put the sun behind the panorama centre so the anti-solar point is in
        # the middle of the sampled dome.
        cls.sun = np.array([-np.cos(np.deg2rad(25.0)),
                            np.sin(np.deg2rad(25.0)), 0.0])
        cls.angle = np.degrees(
            np.arccos(np.clip(cls.rays @ (-cls.sun), -1.0, 1.0)))

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
        cls.renderer.check('secondary rainbow')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Secondary bow must be stable')

    def test_arc_sits_outside_the_primary(self):
        image = self.image()
        arc = self.peak(image, np.abs(self.angle - 51.7) < 1.2)
        primary = self.peak(image, np.abs(self.angle - 42.0) < 2.0)
        far = self.peak(image, np.abs(self.angle - 62.0) < 2.0)
        self.assertGreater(arc, 0.01, 'The secondary bow must be drawn')
        self.assertLess(primary, 1e-7, 'No false arc at the primary radius')
        self.assertLess(far, 1e-7, 'No arc beyond the secondary band')

    def test_colours_are_reversed(self):
        image = self.image()
        inner = image[(self.angle > 50.8) & (self.angle < 51.2)]
        outer = image[(self.angle > 53.3) & (self.angle < 53.8)]
        red_in, blue_in = inner[:, 0].mean(), inner[:, 2].mean()
        red_out, blue_out = outer[:, 0].mean(), outer[:, 2].mean()
        self.assertGreater(red_in, blue_in * 1.3, 'Red belongs on the inner edge')
        self.assertGreater(blue_out, red_out * 1.3, 'Violet belongs outside')

    def test_moisture_gate(self):
        self.assertEqual(float(self.image(moisture=0.0).max()), 0.0)

    def test_day_and_sun_gates(self):
        self.assertEqual(float(self.image(day=0.0).max()), 0.0)
        below = self.image(sun_elevation=-2.0)
        self.assertEqual(float(below.max()), 0.0)

    def test_overcast_dims_the_bow(self):
        clear = float(self.image(overcast=0.0).max())
        cloudy = float(self.image(overcast=0.9).max())
        self.assertGreater(clear, cloudy * 2.0)


if __name__ == '__main__':
    unittest.main()
