"""Compile and branch checks for the top colored-light gather.

COLORED_LIGHT_QUALITY 3 adds a wider, lower-weight second screen-space gather.
The lower profiles keep the single loop.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
void main() {
    vec3 c = screenColoredLight(vec2(0.5), vec3(0.0, 0.0, -4.0),
                                vec3(0.0, 1.0, 0.0));
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source(quality=3):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/colored_light.glsl')
    core = core.replace('#define COLORED_LIGHT_QUALITY 2',
                        f'#define COLORED_LIGHT_QUALITY {quality}')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D colortex0, colortex2, colortex3, depthtex1;\n')
    return head + core + DOMAIN


class ColoredLightHigh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source(3))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def test_top_profile_has_the_wide_gather(self):
        source = shader_source(3)
        self.assertIn('worldRadius*1.65', source)
        self.assertIn('for (int i = 0; i < 6; ++i)', source)
        self.assertIn('depthSimilarity * 0.35', source)

    def test_low_profile_does_not_compile_the_wide_gather(self):
        source = shader_source(1)
        # The source still has the guarded block; check the preprocessor gate
        # rather than pretending the text disappears.
        self.assertIn('#if COLORED_LIGHT_QUALITY >= 3', source)

    def test_top_branch_renders_finite(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        for name, unit, texture in [('colortex0', 0, renderer.buffers[0]),
                                    ('colortex2', 2, renderer.buffers[2]),
                                    ('colortex3', 3, renderer.buffers[3]),
                                    ('depthtex1', 1, renderer.opaque_depth)]:
            renderer.uniform(self.program, name, unit)
            renderer.call('glActiveTexture', None, [U], 0x84C0 + unit)
            renderer.call('glBindTexture', None, [U, U], 0x0DE1, texture)
        renderer.full_screen()
        renderer.check('colored light high')
        data = renderer.read(W, H)[:, :, :3]
        self.assertTrue(np.isfinite(data).all())

    def test_deterministic(self):
        self.assertEqual(shader_source(3), shader_source(3))


if __name__ == '__main__':
    unittest.main()
