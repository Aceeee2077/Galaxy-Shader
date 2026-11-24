"""GPU checks for the dual-radius top-profile bloom blur.

The high profile blends a four-pixel and an eight-pixel blur. A constant field
must keep the same mean; the real composite programs must select both radii.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 16, 16
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform sampler2D src;
uniform vec2 testRes;
uniform float testScale;
void main() {
    vec2 uv = gl_FragCoord.xy / testRes;
    vec3 c = gaussianBlur(src, uv, vec2(0.01 * testScale, 0.0));
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/bloom.glsl')
    core = core.replace('#define BLOOM_QUALITY 2', '#define BLOOM_QUALITY 3')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class BloomHigh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.white = cls.renderer.texture(1, 1, data=np.full((1, 1, 4), 0.5, np.float32))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def image(self, scale):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'src', 0)
        renderer.uniform(self.program, 'testRes', [W, H])
        renderer.uniform(self.program, 'testScale', float(scale))
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, self.white)
        renderer.full_screen()
        renderer.check('bloom high')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_two_radii_preserve_a_constant_field(self):
        np.testing.assert_allclose(self.image(1.0), self.image(2.0), atol=5e-3)

    def test_real_composites_blend_both_radii(self):
        for name in ('composite2.fsh', 'composite3.fsh'):
            source = (SHADERS / 'program' / name).read_text(encoding='utf-8')
            self.assertIn('*8.0', source)
            self.assertIn('mix(narrow,wide,0.35)', source)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(2.0), self.image(2.0))


if __name__ == '__main__':
    unittest.main()
