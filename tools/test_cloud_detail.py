"""GPU checks for the top-profile cloud erosion pass.

CLOUD_QUALITY 4 adds a second fine erosion octave to view samples. The top and
high profiles should differ in density while both stay bounded.
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
void main() {
    float d = cloudDensity3D(testPoint, false, 1.0);
    gl_FragColor = vec4(vec3(d), 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/clouds.glsl')
    core = core.replace('#define CLOUD_QUALITY 3', f'#define CLOUD_QUALITY {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class CloudDetail(unittest.TestCase):
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
    def sample(cls, program, point):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testPoint', list(point))
        renderer.uniform(program, 'frameTimeCounter', 12.0)
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'currentDate', [1, 6, 1])
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'sunPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'shadowLightPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'moonPosition', [0.0, -1.0, 0.0])
        renderer.full_screen()
        renderer.check('cloud detail')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_top_profile_adds_fine_erosion(self):
        points = [(0.0, 215.0, 0.0), (40.0, 235.0, -30.0), (-80.0, 260.0, 70.0)]
        differences = [abs(self.sample(self.top, p) - self.sample(self.high, p))
                       for p in points]
        self.assertGreater(max(differences), 1e-3)

    def test_density_stays_bounded(self):
        for point in [(0.0, 215.0, 0.0), (40.0, 235.0, -30.0)]:
            value = self.sample(self.top, point)
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_top_profile_has_the_extra_erosion(self):
        source = shader_source(4)
        self.assertIn('q*16.2-3.0', source)
        self.assertIn('#if CLOUD_QUALITY >= 4', source)


if __name__ == '__main__':
    unittest.main()
