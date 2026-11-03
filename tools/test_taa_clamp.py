"""GPU checks for the five-tap TAA history clamp at the low profile.

At TAA_QUALITY 1 the clamp now reads the centre and four edge neighbours; the
diagonals are the taps least likely to catch a moving edge, saving four texture
fetches per resolved pixel. The fixture puts a different value only on the
four diagonal neighbours, so the low profile must ignore it while quality 2
must still include it.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
UV = (4.5 / W, 4.5 / H)
EDGE_VALUE = 0.5
DIAGONAL_VALUE = 0.2


def clamp_source(quality, history):
    source = ('#version 330 compatibility\n#define DIMENSION 0\n' +
              expand(SHADERS / 'lib/common.glsl') +
              'uniform sampler2D colortex0, colortex3, colortex7, depthtex0;\n' +
              expand(SHADERS / 'lib/taa.glsl') +
              f'''
uniform vec2 testUV;
void main() {{
    gl_FragColor = vec4(clampTemporalHistory(colortex0, testUV, vec3({history})), 1.0);
}}''')
    return source.replace('#define TAA_QUALITY 3',
                          f'#define TAA_QUALITY {quality}')


def fixture_texture(renderer):
    data = np.full((H, W, 4), 1.0, np.float32)
    data[..., :3] = EDGE_VALUE
    for x, y in ((3, 3), (5, 3), (3, 5), (5, 5)):
        data[y, x, :3] = DIAGONAL_VALUE
    return renderer.texture(W, H, data=data)


class TaaClampRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.texture = fixture_texture(cls.renderer)
        cls.low_below = cls.renderer.gl.compile(VERTEX, clamp_source(1, '0.1'))
        cls.low_above = cls.renderer.gl.compile(VERTEX, clamp_source(1, '0.7'))
        cls.high_below = cls.renderer.gl.compile(VERTEX, clamp_source(2, '0.1'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.low_below, cls.low_above, cls.high_below):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'viewWidth', float(W))
        cls.renderer.uniform(program, 'viewHeight', float(H))
        cls.renderer.uniform(program, 'testUV', list(UV))
        cls.renderer.call('glActiveTexture', None, [U], 0x84C0)
        cls.renderer.call('glBindTexture', None, [U, U], 0x0DE1, cls.texture)
        cls.renderer.uniform(program, 'colortex0', 0)
        cls.renderer.full_screen()
        cls.renderer.check('taa clamp')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_low_profile_ignores_diagonals(self):
        data = self.image(self.low_below)
        np.testing.assert_allclose(data, EDGE_VALUE, atol=2e-4,
                                   err_msg='Low TAA must read only the cross')

    def test_low_profile_clamps_above(self):
        np.testing.assert_allclose(self.image(self.low_above), EDGE_VALUE,
                                   atol=2e-4)

    def test_high_profile_keeps_diagonals(self):
        data = self.image(self.high_below)
        np.testing.assert_allclose(data, DIAGONAL_VALUE, atol=2e-4,
                                   err_msg='Quality 2 must keep the 3x3 box')

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(self.low_below),
                                      self.image(self.low_below))


if __name__ == '__main__':
    unittest.main()
