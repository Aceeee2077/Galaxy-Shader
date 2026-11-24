"""GPU checks for the top-profile water chromatic refraction.

The helper samples red and blue on opposite sides of the refracted UV and green
on the physical UV. A horizontal red/blue gradient makes the separation visible
without requiring the full game pipeline.
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
uniform vec2 testOffset;
void main() {
    vec2 uv = gl_FragCoord.xy / testRes;
    gl_FragColor = vec4(chromaticRefraction(src, uv, testOffset), 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/water.glsl')
    core = core.replace('#define WATER_QUALITY 2', '#define WATER_QUALITY 3')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class WaterChroma(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())
        y, x = np.mgrid[0:H, 0:W]
        data = np.zeros((H, W, 4), np.float32)
        data[:, :, 0] = x / float(W - 1)
        data[:, :, 1] = 0.5
        data[:, :, 2] = x / float(W - 1)
        data[:, :, 3] = 1.0
        cls.gradient = cls.renderer.texture(W, H, data=data)

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def image(self, offset):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'viewWidth', float(W))
        renderer.uniform(self.program, 'viewHeight', float(H))
        renderer.uniform(self.program, 'testRes', [W, H])
        renderer.uniform(self.program, 'testOffset', list(offset))
        renderer.uniform(self.program, 'src', 0)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, self.gradient)
        renderer.full_screen()
        renderer.check('water chroma')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_red_and_blue_separate(self):
        center = self.image((0.0, 0.0))
        shifted = self.image((0.12, 0.0))
        c = center[::4, ::4]
        s = shifted[::4, ::4]
        self.assertGreater(float(s[:, :, 0].mean()), float(c[:, :, 0].mean()) + 0.03)
        self.assertLess(float(s[:, :, 2].mean()), float(c[:, :, 2].mean()) - 0.03)
        np.testing.assert_allclose(s[:, :, 1], c[:, :, 1], atol=1e-3)

    def test_zero_offset_matches_a_plain_sample(self):
        center = self.image((0.0, 0.0))
        np.testing.assert_allclose(center[:, :, 0], center[:, :, 2], atol=1e-3)

    def test_top_profile_uses_the_helper(self):
        source = (SHADERS / 'program' / 'translucent.fsh').read_text(encoding='utf-8')
        self.assertIn('WATER_QUALITY >= 3', source)
        self.assertIn('chromaticRefraction(colortex4,refrUV,chroma)', source)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image((0.12, 0.0)), self.image((0.12, 0.0)))


if __name__ == '__main__':
    unittest.main()
