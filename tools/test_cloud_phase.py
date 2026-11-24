"""GPU checks for the top-profile dual-lobe cloud phase function.

CLOUD_QUALITY 4 blends a broad multiple-scattering lobe into the sharp forward
lobe. The fixture compares the helper at several scattering angles and checks
that the top profile stays finite, positive and distinct from the lower one.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform float testCos;
void main() {
    gl_FragColor = vec4(vec3(cloudPhase(testCos)), 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/clouds.glsl')
    core = core.replace('#define CLOUD_QUALITY 3', f'#define CLOUD_QUALITY {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class CloudPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.top = cls.renderer.gl.compile(VERTEX, shader_source(4))
        cls.high = cls.renderer.gl.compile(VERTEX, shader_source(3))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.top, cls.high):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, cos_theta):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testCos', float(cos_theta))
        renderer.full_screen()
        renderer.check('cloud phase')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_top_phase_is_positive_at_all_angles(self):
        for cos_theta in (-1.0, -0.5, 0.0, 0.5, 1.0):
            value = self.sample(self.top, cos_theta)
            self.assertGreater(value, 0.0)
            self.assertLess(value, 5.0)

    def test_top_phase_differs_from_the_single_lobe(self):
        differences = [abs(self.sample(self.top, c) - self.sample(self.high, c))
                       for c in (-1.0, 0.0, 1.0)]
        self.assertGreater(max(differences), 0.01)

    def test_deterministic(self):
        self.assertEqual(self.sample(self.top, 0.3), self.sample(self.top, 0.3))


if __name__ == '__main__':
    unittest.main()
