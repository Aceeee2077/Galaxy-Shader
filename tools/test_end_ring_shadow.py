"""GPU checks for the End giant's ring shadow.

The helper traces a surface-to-star line through the ring plane and darkens the
planet only when it crosses the annulus. Points outside the ring stay lit.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform vec3 testPoint;
uniform vec3 testStar;
void main() {
    float s = endRingShadow(testPoint, vec3(0.0), testStar, vec3(0.0, 1.0, 0.0));
    gl_FragColor = vec4(vec3(s), 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/end_sky.glsl')
    return '#version 330 compatibility\n#define DIMENSION 1\n' + core + DOMAIN


class EndRingShadow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def sample(self, point, star):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        renderer.uniform(self.program, 'testPoint', list(point))
        renderer.uniform(self.program, 'testStar', list(star))
        renderer.full_screen()
        renderer.check('end ring shadow')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_ring_annulus_darkens_the_planet(self):
        value = self.sample((0.0, 13.0, 0.0), (100.0, -20.0, 0.0))
        self.assertLess(value, 0.9)
        self.assertGreater(value, 0.3)

    def test_star_overhead_leaves_the_planet_lit(self):
        self.assertAlmostEqual(self.sample((0.0, 13.0, 0.0), (0.0, -100.0, 0.0)),
                               1.0, places=4)

    def test_ring_is_used_on_the_planet(self):
        source = (SHADERS / 'lib/end_sky.glsl').read_text(encoding='utf-8')
        self.assertIn('lit*=endRingShadow(ray*planetHit,center,starCenter,ringNormal);',
                      source)

    def test_deterministic(self):
        self.assertEqual(self.sample((0.0, 13.0, 0.0), (100.0, -20.0, 0.0)),
                         self.sample((0.0, 13.0, 0.0), (100.0, -20.0, 0.0)))


if __name__ == '__main__':
    unittest.main()
