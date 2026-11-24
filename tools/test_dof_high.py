"""GPU checks for the top-profile DOF aperture weight.

DOF_QUALITY 3 weights the outer ring more than the centre; lower profiles keep
a uniform disc. The helper is pure and the real camera-effects source compiles.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform vec2 testDisk;
void main() {
    gl_FragColor = vec4(vec3(dofApertureWeight(testDisk)), 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/camera_effects.glsl')
    core = core.replace('#define DOF_QUALITY 0', f'#define DOF_QUALITY {quality}')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform sampler2D colortex0, colortex3, depthtex0;\n')
    return head + core + DOMAIN


class DofHigh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.top = cls.renderer.gl.compile(VERTEX, shader_source(3))
        cls.low = cls.renderer.gl.compile(VERTEX, shader_source(2))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.top, cls.low):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, disk):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testDisk', list(disk))
        renderer.full_screen()
        renderer.check('dof high')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_top_profile_weights_the_outer_ring(self):
        center = self.sample(self.top, (0.0, 0.0))
        edge = self.sample(self.top, (0.95, 0.0))
        self.assertAlmostEqual(center, 0.55, places=3)
        self.assertGreater(edge, center)
        self.assertLessEqual(edge, 1.0)

    def test_lower_profile_keeps_a_uniform_disc(self):
        self.assertEqual(self.sample(self.low, (0.0, 0.0)), 1.0)
        self.assertEqual(self.sample(self.low, (0.95, 0.0)), 1.0)

    def test_top_profile_uses_the_helper(self):
        source = (SHADERS / 'lib/camera_effects.glsl').read_text(encoding='utf-8')
        self.assertIn('DOF_QUALITY >= 3', source)
        self.assertIn('dofApertureWeight(disk)', source)


if __name__ == '__main__':
    unittest.main()
