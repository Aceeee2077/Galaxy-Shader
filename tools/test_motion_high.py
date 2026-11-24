"""Compile and branch checks for the top motion-blur reconstruction.

MOTION_BLUR 3 uses up to fifteen taps with a triangular shutter weight; lower
profiles keep the existing uniform taps. The fixture compiles the top branch.
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
    vec3 c = cameraEffects(vec2(0.5), vec3(0.5));
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source(quality=3):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/camera_effects.glsl')
    core = core.replace('#define MOTION_BLUR 0', f'#define MOTION_BLUR {quality}')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D colortex0, colortex3, depthtex0;\n')
    return head + core + DOMAIN


class MotionHigh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source(3))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def test_top_profile_uses_triangular_weights(self):
        source = shader_source(3)
        self.assertIn('for(int i=1;i<16;++i)', source)
        self.assertIn('float w=1.0-abs(float(i)/float(count)-0.5)', source)
        self.assertIn('#if MOTION_BLUR >= 3', source)

    def test_top_branch_renders_finite(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        for name, unit, texture in [('colortex0', 0, renderer.buffers[0]),
                                    ('colortex3', 3, renderer.buffers[3]),
                                    ('depthtex0', 1, renderer.depth)]:
            renderer.uniform(self.program, name, unit)
            renderer.call('glActiveTexture', None, [U], 0x84C0 + unit)
            renderer.call('glBindTexture', None, [U, U], 0x0DE1, texture)
        renderer.full_screen()
        renderer.check('motion high')
        data = renderer.read(W, H)[:, :, :3]
        self.assertTrue(np.isfinite(data).all())

    def test_deterministic(self):
        self.assertEqual(shader_source(3), shader_source(3))


if __name__ == '__main__':
    unittest.main()
