"""GPU checks for the top-profile rough-reflection blur.

The highest SSR profile uses four axis taps plus the centre instead of the
cheap diagonal cross. A constant hit field must preserve its value.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform sampler2D scene;
uniform vec2 testUV;
uniform vec2 testBlur;
void main() {
    vec3 c = blurRoughReflection(scene, testUV, testBlur, texture2D(scene, testUV).rgb);
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/reflections.glsl')
    core = core.replace('#define SSR_QUALITY 2', '#define SSR_QUALITY 4')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class SsrRough(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.white = cls.renderer.texture(1, 1, data=np.full((1, 1, 4), 0.5, np.float32))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def image(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'scene', 0)
        renderer.uniform(self.program, 'testUV', [0.5, 0.5])
        renderer.uniform(self.program, 'testBlur', [0.02, 0.02])
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, self.white)
        renderer.full_screen()
        renderer.check('ssr rough')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_constant_hit_is_preserved(self):
        np.testing.assert_allclose(self.image(), 0.5, atol=5e-3)

    def test_top_profile_uses_four_axis_taps(self):
        source = shader_source()
        self.assertIn('#if SSR_QUALITY >= 4', source)
        self.assertIn('vec2(blur.x, 0.0)', source)
        self.assertIn('vec2(0.0, blur.y)', source)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(), self.image())


if __name__ == '__main__':
    unittest.main()
