"""GPU checks for the top-profile water capillary detail.

WATER_QUALITY 3 adds a second high-frequency slope train; lower profiles keep
the existing two-wave plus one capillary field.
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
    vec3 n = waterNormal(vec3(12.0, 0.0, 18.0), vec3(0.0, 1.0, 0.0), 5.0);
    gl_FragColor = vec4(n * 0.5 + 0.5, 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/water.glsl')
    core = core.replace('#define WATER_QUALITY 2', f'#define WATER_QUALITY {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class WaterDetail(unittest.TestCase):
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
    def sample(cls, program):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'frameTimeCounter', 12.0)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.full_screen()
        renderer.check('water detail')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_top_profile_adds_detail(self):
        top = self.sample(self.top)
        low = self.sample(self.low)
        self.assertGreater(float(np.abs(top - low).max()), 1e-3)

    def test_top_detail_stays_close(self):
        top = self.sample(self.top)
        low = self.sample(self.low)
        self.assertLess(float(np.abs(top - low).max()), 0.08)

    def test_source_has_the_third_train(self):
        source = (SHADERS / 'lib/water.glsl').read_text(encoding='utf-8')
        self.assertIn('world.x*9.3-world.z*2.1+t*3.7', source)
        self.assertIn('#if WATER_QUALITY >= 3', source)


if __name__ == '__main__':
    unittest.main()
