"""GPU checks for star colour temperature and magnitude.

The fixture samples the authored starColour mapping over a two-hash grid. It is
an engineering check, not a Minecraft screenshot or a stellar spectrum.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 256, 256
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


class StarColourRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/star_color.glsl') +
                    '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    gl_FragColor = vec4(starColour(uv.x, uv.y), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls):
        cls.renderer.full_screen()
        cls.renderer.check('star colour')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(), self.image(),
                                      'Star colours must be stable')

    def test_warm_and_cool_ends(self):
        image = self.image()
        warm = image[2]   # temperature hash near 0
        cool = image[-3]  # temperature hash near 1
        self.assertGreater(float(warm[:, 0].mean()),
                           float(warm[:, 2].mean()) * 1.20,
                           'Cool-temperature hash must lean red')
        self.assertGreater(float(cool[:, 2].mean()),
                           float(cool[:, 0].mean()) * 1.15,
                           'Hot-temperature hash must lean blue')

    def test_temperature_changes_smoothly(self):
        image = self.image().mean(axis=1)
        balance = image[:, 2] - image[:, 0]
        self.assertTrue(np.all(np.diff(balance) >= -1e-6),
                        'Blue-minus-red must rise monotonically with temperature')

    def test_magnitude_spreads_brightness(self):
        image = self.image().mean(axis=2)
        faint = float(image[:, 5].mean())
        bright = float(image[:, -6].mean())
        self.assertGreater(bright, faint * 1.4,
                           'The magnitude hash must alter brightness')

    def test_bounded_output(self):
        image = self.image()
        self.assertGreaterEqual(float(image.min()), 0.30)
        self.assertLessEqual(float(image.max()), 1.40)


if __name__ == '__main__':
    unittest.main()
