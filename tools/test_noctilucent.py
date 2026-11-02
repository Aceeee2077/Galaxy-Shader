"""GPU checks for the analytic noctilucent-cloud layer.

The fixture samples the authored sky function over a synthetic upper hemisphere.
It is an engineering check, not a Minecraft screenshot or weather simulation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 160, 96
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
LOW = np.s_[0:40, :]
TOP = np.s_[88:, :]


class NoctilucentRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/noctilucent.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testSummer;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.70;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = noctilucentClouds(ray, normalize(testSun),
                                   testOvercast, testSummer);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_height, summer=1.0, overcast=0.0, time=80.0):
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        cls.renderer.uniform(cls.program, 'testSun',
                             [horizontal, sun_height, 0.0])
        cls.renderer.uniform(cls.program, 'testSummer', summer)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('noctilucent clouds')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, region=None):
        return float((image if region is None else image[region]).max())

    def test_deterministic(self):
        a = self.image(-0.18, time=321.0)
        b = self.image(-0.18, time=321.0)
        np.testing.assert_array_equal(a, b, 'Cloud sheet must be stable')

    def test_daylight_and_deep_night_gate(self):
        self.assertLess(self.peak(self.image(0.20)), 1e-7)
        self.assertLess(self.peak(self.image(-0.75)), 1e-7)

    def test_twilight_window_and_blue_colour(self):
        image = self.image(-0.18)
        self.assertGreater(self.peak(image), 0.004)
        active = image[image[:, :, 2] > 0.001]
        red, green, blue = (float(active[:, c].mean()) for c in range(3))
        self.assertGreater(blue, red * 1.35, 'NLC must read electric blue')
        self.assertGreater(blue, green, 'Blue stays the dominant channel')

    def test_overcast_suppresses_the_layer(self):
        clear = self.image(-0.18, overcast=0.0)
        cloudy = self.image(-0.18, overcast=1.0)
        self.assertGreater(self.peak(clear), 0.004)
        self.assertLess(self.peak(cloudy), 1e-7)

    def test_summer_strengthens_the_layer(self):
        summer = self.peak(self.image(-0.18, summer=1.0))
        spring = self.peak(self.image(-0.18, summer=0.0))
        self.assertGreater(summer, spring * 1.5)

    def test_layer_stays_low_and_structured(self):
        image = self.image(-0.18)
        self.assertGreater(self.peak(image, LOW), 0.004)
        self.assertLess(self.peak(image, TOP), 1e-6,
                        'No haze above the top of the layer')
        active = image[:, :, 2][image[:, :, 2] > 0.001]
        self.assertGreater(float(active.std()), float(active.mean()) * 0.18,
                           'Bands must not be a uniform blue wash')


if __name__ == '__main__':
    unittest.main()
