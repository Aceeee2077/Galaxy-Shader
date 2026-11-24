"""GPU checks for the high-profile volumetric multiple-scattering tail.

The tail is zero for a fully shadowed path, increases with mean visibility and
is only enabled above VOLUMETRIC_QUALITY 2.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform float testMean;
void main() {
    gl_FragColor = vec4(vec3(volumetricMultipleScatter(testMean)), 1.0);
}'''


def shader_source(quality=3):
    core = (expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/lighting.glsl') +
            expand(SHADERS / 'lib/volumetrics.glsl'))
    core = core.replace('#define VOLUMETRIC_QUALITY 2',
                        f'#define VOLUMETRIC_QUALITY {quality}')
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            '#define vCloudShadow 1.0\n') + core + DOMAIN


class VolumetricMulti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source(3))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def sample(self, mean):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'testMean', float(mean))
        renderer.full_screen()
        renderer.check('volumetric multi')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_zero_for_a_dark_path(self):
        self.assertEqual(self.sample(0.0), 0.0)

    def test_grows_with_visibility(self):
        values = [self.sample(x) for x in (0.1, 0.4, 0.8, 1.0)]
        self.assertEqual(values, sorted(values))
        self.assertGreater(values[-1], values[0])

    def test_high_profile_enables_the_tail(self):
        source = shader_source(3)
        self.assertIn('#if VOLUMETRIC_QUALITY >= 3', source)
        self.assertIn('volumetricMultipleScatter(mean)', source)
        self.assertEqual(source.count('#if VOLUMETRIC_QUALITY >= 3'), 1)

    def test_deterministic(self):
        self.assertEqual(self.sample(0.6), self.sample(0.6))


if __name__ == '__main__':
    unittest.main()
