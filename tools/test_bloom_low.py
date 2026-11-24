"""GPU checks for the low-profile bloom footprint.

BLOOM_QUALITY 1 now averages a 2x2 bright-pass footprint and uses a normalized
three-tap blur instead of the 4x4 / five-tap path. A constant field must keep
the same value, so the change removes fetches without changing bloom energy.
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
uniform float mode;
void main() {
    vec2 uv = gl_FragCoord.xy / testRes;
    vec3 c = texture2D(src, uv).rgb;
    vec3 result;
    if (mode < 0.5) result = vec3(brightPass(c));
    else if (mode < 1.5) result = gaussianBlurLow(src, uv, vec2(0.01, 0.0));
    else result = gaussianBlur(src, uv, vec2(0.01, 0.0));
    gl_FragColor = vec4(result, 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/bloom.glsl')
    core = core.replace('#define BLOOM_QUALITY 2', '#define BLOOM_QUALITY 1')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class BloomLow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.white = cls.renderer.texture(1, 1, data=np.full((1, 1, 4), 0.5, np.float32))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def image(self, mode):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'src', 0)
        renderer.uniform(self.program, 'testRes', [W, H])
        renderer.uniform(self.program, 'mode', mode)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, self.white)
        renderer.full_screen()
        renderer.check('bloom low')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_low_blur_preserves_a_constant_field(self):
        low = self.image(1.0)
        full = self.image(2.0)
        np.testing.assert_allclose(low, full, atol=5e-3)

    def test_bright_pass_is_stable_on_a_constant_field(self):
        data = self.image(0.0)
        np.testing.assert_allclose(data, np.full_like(data, data.mean()), atol=5e-3)

    def test_low_profile_uses_the_smaller_kernel(self):
        source = shader_source()
        self.assertIn('for(int y=0;y<2;++y) for(int x=0;x<2;++x)', (SHADERS / 'program' / 'composite1.fsh').read_text(encoding='utf-8'))
        self.assertIn('gaussianBlurLow', (SHADERS / 'program' / 'composite2.fsh').read_text(encoding='utf-8'))
        self.assertIn('gaussianBlurLow', (SHADERS / 'program' / 'composite3.fsh').read_text(encoding='utf-8'))
        self.assertIn('*0.5', source)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(1.0), self.image(1.0))


if __name__ == '__main__':
    unittest.main()
