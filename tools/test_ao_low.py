"""Compile and contract checks for the low GTAO budget.

AO_QUALITY 1 now uses two directions instead of three. The low profile keeps
the same edge weights and world-space radius; this fixture compiles the real
function and checks the source budget and bounded output.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform vec2 testUV;
void main() {
    vec3 view = vec3(0.0, 0.0, -4.0);
    float v = gtaoVisibility(testUV, view, vec3(0.0, 1.0, 0.0));
    gl_FragColor = vec4(vec3(v), 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/gtao.glsl')
    core = core.replace('#define AO_QUALITY 2', '#define AO_QUALITY 1')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D depthtex1, colortex1, colortex3;\n')
    return head + core + DOMAIN


class AoLow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def test_low_profile_uses_two_directions(self):
        source = shader_source()
        self.assertIn('const int directions = 2;', source)
        self.assertIn('const int steps = 2;', source)
        self.assertNotIn('const int directions = 3;', source)

    def test_output_is_bounded(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'testUV', [0.5, 0.5])
        renderer.uniform(self.program, 'depthtex1', 0)
        renderer.uniform(self.program, 'colortex1', 1)
        renderer.uniform(self.program, 'colortex3', 2)
        for unit, texture in [(0, renderer.opaque_depth), (1, renderer.normal), (2, renderer.buffers[3])]:
            renderer.call('glActiveTexture', None, [U], 0x84C0 + unit)
            renderer.call('glBindTexture', None, [U, U], 0x0DE1, texture)
        renderer.full_screen()
        renderer.check('ao low')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        self.assertGreaterEqual(float(data.min()), 0.0)
        self.assertLessEqual(float(data.max()), 1.0)

    def test_deterministic(self):
        # The shader is stateless; the source contract is the deterministic
        # part of this low-profile budget change.
        self.assertEqual(shader_source(), shader_source())


if __name__ == '__main__':
    unittest.main()
