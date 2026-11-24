"""GPU checks for the fixed four-tap PCF kernel in the low shadow profile.

The low profile has no blocker search, so its filter radius is constant. The
old code still rotated the kernel with valueNoise and sin/cos per pixel. The
probe counts noise calls in the real `shadowVisibility` and checks that the new
fixed cross plus 2x2 jitter still produces a stable, non-empty penumbra.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 32, 32
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 player = vec3((uv.x - 0.5) * 16.0, 0.0, (uv.y - 0.5) * 16.0);
    float v = shadowVisibility(player, vec3(0.0, 1.0, 0.0), true);
    gl_FragColor = vec4(vec3(v), noiseCalls);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/shadows.glsl')
    core = core.replace('#define SHADOW_QUALITY 3', '#define SHADOW_QUALITY 1')
    definition = 'float valueNoise(vec2 p) {'
    renamed = 'float valueNoiseCore(vec2 p) {'
    assert core.count(definition) == 1
    core = core.replace(definition, renamed)
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float noiseCalls=0.0;\nfloat valueNoise(vec2 p);\n')
    wrapper = '''
float valueNoise(vec2 p) {
    noiseCalls += 1.0;
    return valueNoiseCore(p);
}
'''
    return head + core + wrapper + DOMAIN


class ShadowLowKernel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())
        y, x = np.mgrid[0:64, 0:64]
        depth = np.zeros((64, 64, 4), np.float32)
        depth[:, :, :3] = (0.42 + 0.10 * np.sin(x * 0.35) * np.cos(y * 0.22))[:, :, None]
        depth[:, :, 3] = 1.0
        cls.depth = cls.renderer.texture(64, 64, data=depth)

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def image(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        for name in ('gbufferModelView', 'gbufferModelViewInverse',
                     'shadowModelView'):
            renderer.uniform(self.program, name, np.eye(4, dtype=np.float32))
        renderer.uniform(self.program, 'shadowProjection',
                         np.diag([0.05, 0.05, 0.05, 1.0]).astype(np.float32))
        renderer.uniform(self.program, 'shadowtex0', 0)
        renderer.uniform(self.program, 'testResolution', [W, H])
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, self.depth)
        renderer.full_screen()
        renderer.check('shadow low kernel')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_low_kernel_does_not_call_value_noise(self):
        data = self.image()
        self.assertEqual(float(data[:, :, 3].sum()), 0.0)

    def test_low_kernel_still_produces_a_penumbra(self):
        data = self.image()[:, :, 0]
        self.assertGreaterEqual(float(data.min()), 0.0)
        self.assertLessEqual(float(data.max()), 1.0)
        self.assertGreater(float(data.max() - data.min()), 0.05)

    def test_low_kernel_source_has_no_rotation_noise(self):
        source = shader_source()
        start = source.index('#if SHADOW_QUALITY == 1')
        end = source.index('#else', start)
        low = source[start:end]
        self.assertNotIn('valueNoise(', low)
        self.assertNotIn('cos(', low)
        self.assertNotIn('sin(', low)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(), self.image())


if __name__ == '__main__':
    unittest.main()
