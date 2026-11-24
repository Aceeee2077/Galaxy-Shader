"""Compile and budget checks for the low SSR profile.

SSR_QUALITY 1 now takes six adaptive steps instead of eight. The fixture checks
the real low branch compiles and the source keeps the reduced budget.
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
    vec4 r = traceReflection(colortex0, vec3(0.0, 0.0, -4.0),
                             vec3(0.0, 1.0, 0.0), 0.05);
    gl_FragColor = vec4(r.rgb, 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/reflections.glsl')
    core = core.replace('#define SSR_QUALITY 2', '#define SSR_QUALITY 1')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D colortex0;\n')
    return head + core + DOMAIN


class SsrLow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def test_low_profile_uses_six_steps(self):
        source = shader_source()
        self.assertIn('const int count=6;', source)
        self.assertIn('const float maxDistance=34.0;', source)
        self.assertNotIn('const int count=8;', source)

    def test_low_branch_compiles_and_is_finite(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'colortex0', 0)
        renderer.uniform(self.program, 'depthtex1', 1)
        for unit, texture in [(0, renderer.buffers[0]), (1, renderer.opaque_depth)]:
            renderer.call('glActiveTexture', None, [U], 0x84C0 + unit)
            renderer.call('glBindTexture', None, [U, U], 0x0DE1, texture)
        renderer.full_screen()
        renderer.check('ssr low')
        data = renderer.read(W, H)[:, :, :3]
        self.assertTrue(np.isfinite(data).all())


if __name__ == '__main__':
    unittest.main()
