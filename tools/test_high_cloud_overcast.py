"""GPU checks for the overcast early-out in the high cirrus layer.

The cirrus alpha is multiplied by (1 - overcast), which is exactly zero under
a full overcast deck. The layer must return the incoming sky untouched there,
while clear weather must still draw it.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = 32
H = 16
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
SKY = (0.10, 0.20, 0.30)
RAY = (0.0, 0.35, 0.94)
ORIGIN = (0.0, 70.0, 0.0)


def source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/clouds.glsl') +
            '''
void main() {
    vec3 sky = vec3(0.10, 0.20, 0.30);
    gl_FragColor = vec4(highCloudLayer(sky, normalize(vec3(0.0, 0.35, 0.94)),
                                      vec3(0.0, 70.0, 0.0)), 1.0);
}''')


class HighCloudOvercastRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, source())

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, rain, thunder, wetness):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'rainStrength', rain)
        cls.renderer.uniform(cls.program, 'thunderStrength', thunder)
        cls.renderer.uniform(cls.program, 'wetness', wetness)
        cls.renderer.uniform(cls.program, 'sunPosition', [0.0, 70.0, 71.0])
        cls.renderer.uniform(cls.program, 'moonPosition', [0.0, -70.0, -71.0])
        cls.renderer.uniform(cls.program, 'frameTimeCounter', 0.0)
        cls.renderer.uniform(cls.program, 'frameCounter', 0)
        cls.renderer.full_screen()
        cls.renderer.check('high cloud overcast')
        return cls.renderer.read(W, H)[:, :, :3]

    def test_full_overcast_returns_sky(self):
        np.testing.assert_allclose(
            self.image(1.0, 1.0, 1.0),
            np.broadcast_to(np.array(SKY, np.float32), (H, W, 3)), atol=2e-4,
            err_msg='A fully overcast sky must skip the cirrus layer exactly')

    def test_clear_weather_keeps_cirrus(self):
        clear = self.image(0.0, 0.0, 0.0)
        self.assertGreater(float(np.abs(clear - np.array(SKY)).max()), 1e-4,
                           'Clear weather must keep the cirrus veil')

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(0.0, 0.0, 0.0),
                                      self.image(0.0, 0.0, 0.0))


if __name__ == '__main__':
    unittest.main()
