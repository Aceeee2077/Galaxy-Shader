"""GPU checks for the top-profile wind-wave crest foam.

Calm water and a flat noise crest must produce exactly zero foam; a steep slope
with a broken crest produces more in a storm than in clear weather.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform vec2 testSlope;
uniform float testNoise;
uniform float testStorm;
void main() {
    gl_FragColor = vec4(vec3(crestFoamAmount(testSlope, testNoise, testStorm)), 1.0);
}'''


def shader_source():
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/water.glsl')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class WaterCrest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source())

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def sample(cls, slope, noise, storm):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], cls.program)
        renderer.uniform(cls.program, 'testSlope', list(slope))
        renderer.uniform(cls.program, 'testNoise', float(noise))
        renderer.uniform(cls.program, 'testStorm', float(storm))
        renderer.full_screen()
        renderer.check('water crest')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_calm_water_has_no_foam(self):
        self.assertEqual(self.sample((0.0, 0.0), 1.0, 1.0), 0.0)
        self.assertEqual(self.sample((0.3, 0.0), 0.0, 1.0), 0.0)

    def test_storm_has_more_foam_than_clear_weather(self):
        clear = self.sample((0.35, 0.0), 0.9, 0.0)
        storm = self.sample((0.35, 0.0), 0.9, 1.0)
        self.assertGreater(clear, 0.0)
        self.assertGreater(storm, clear)

    def test_top_profile_uses_the_helper(self):
        source = (SHADERS / 'program' / 'translucent.fsh').read_text(encoding='utf-8')
        self.assertIn('WATER_QUALITY >= 3', source)
        self.assertIn('crestFoamAmount(slope,crestNoise,storm)', source)

    def test_deterministic(self):
        self.assertEqual(self.sample((0.35, 0.0), 0.9, 1.0),
                         self.sample((0.35, 0.0), 0.9, 1.0))


if __name__ == '__main__':
    unittest.main()
