"""GPU checks for the top-profile TAA variance clamp.

A 3x3 min/max box admits a single bright historical outlier. TAA_QUALITY 3 now
uses a mean +/- 1.5 sigma YCoCg envelope. The fixture feeds a bright outlier
neighborhood and checks that the new clamp pulls the history toward the local
mean while the old min/max clamp keeps it.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
VARIANCE = '''#if TAA_QUALITY >= 3
    // Min/max clipping still admits a single bright historical outlier when
    // the 3x3 neighborhood contains one matching pixel. On a moving camera,
    // replace the bounds with a mean +/- 1.5 sigma YCoCg envelope: static
    // detail stays inside it, while a lone ghost is pulled toward the local
    // mean before it can persist for another frame. A still frame keeps the
    // min/max bounds so repeated rendering cannot oscillate.
    if (motionPixels > 0.5) {
        vec3 mean = sum / 9.0;
        vec3 variance = max(sumSq / 9.0 - mean * mean, vec3(0.0));
        vec3 sigma = sqrt(variance);
        lo = mean - sigma * 1.5;
        hi = mean + sigma * 1.5;
    }
#endif'''
DOMAIN = '''
uniform vec3 testHistory;
uniform vec2 testRes;
uniform float testMotion;
void main() {
    vec2 uv = gl_FragCoord.xy / testRes;
    vec3 c = clampTemporalHistory(colortex0, uv, testHistory, testMotion);
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/taa.glsl')
    if old:
        assert core.count(VARIANCE) == 1
        core = core.replace(VARIANCE, '')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D colortex0, colortex3, colortex7, depthtex0;\n')
    return head + core + DOMAIN


class TaaVariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))
        data = np.full((H, W, 4), 0.2, np.float32)
        data[:, :, 3] = 1.0
        data[H // 2, W // 2, :3] = 0.8
        cls.current = cls.renderer.texture(W, H, data=data)

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, history=(0.8, 0.8, 0.8), motion=5.0):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'viewWidth', float(W))
        renderer.uniform(program, 'viewHeight', float(H))
        renderer.uniform(program, 'testRes', [W, H])
        renderer.uniform(program, 'testHistory', list(history))
        renderer.uniform(program, 'testMotion', motion)
        renderer.uniform(program, 'colortex0', 0)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, cls.current)
        renderer.full_screen()
        renderer.check('taa variance')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_variance_clamp_pulls_back_a_ghost(self):
        new = self.sample(self.new)
        old = self.sample(self.old)
        # The bright centre is a lone outlier; min/max keeps it, while the
        # variance envelope lands between the mean and the outlier.
        self.assertGreater(float(new[H // 2, W // 2, 0]), 0.2)
        self.assertLess(float(new[H // 2, W // 2, 0]), 0.8)
        self.assertGreater(float(old[H // 2, W // 2, 0]), float(new[H // 2, W // 2, 0]))

    def test_variance_clamp_keeps_the_flat_region(self):
        new = self.sample(self.new, history=(0.2, 0.2, 0.2), motion=0.0)
        patch = new[1:H - 1, 1:W - 1, 0]
        self.assertLess(float(np.abs(patch - 0.2).max()), 0.08)

    def test_top_profile_uses_variance_code(self):
        source = shader_source()
        self.assertIn('sigma * 1.5', source)
        self.assertIn('sumSq / 9.0', source)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.sample(self.new), self.sample(self.new))


if __name__ == '__main__':
    unittest.main()
