"""GPU checks for the analytic polar stratospheric (nacreous) clouds.

The fixture samples the authored sky function over a synthetic upper hemisphere.
It is an engineering check, not a Minecraft screenshot or a cloud simulation.
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


class NacreousRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/nacreous.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testWinter;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.70;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = nacreousClouds(ray, normalize(testSun),
                                testOvercast, testWinter);
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
    def image(cls, sun_height, winter=1.0, overcast=0.0, time=80.0):
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        cls.renderer.uniform(cls.program, 'testSun',
                             [horizontal, sun_height, 0.0])
        cls.renderer.uniform(cls.program, 'testWinter', winter)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('nacreous clouds')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, region=None):
        return float((image if region is None else image[region]).max())

    def test_deterministic(self):
        a = self.image(-0.10, time=321.0)
        b = self.image(-0.10, time=321.0)
        np.testing.assert_array_equal(a, b, 'Cloud sheet must be stable')

    def test_daylight_and_deep_night_gate(self):
        self.assertLess(self.peak(self.image(0.20)), 1e-7)
        self.assertLess(self.peak(self.image(-0.60)), 1e-7)

    def test_twilight_sheet_and_pastel_colour(self):
        image = self.image(-0.10)
        self.assertGreater(self.peak(image), 0.008)
        active = image[image.max(axis=2) > 0.002]
        means = active.mean(axis=0)
        self.assertGreater(means.max(), means.min() * 1.04,
                           'Iridescence must tint the sheet')
        dominant = np.argmax(active, axis=1)
        counts = np.bincount(dominant, minlength=3)
        self.assertTrue((counts > active.shape[0] * 0.08).all(),
                        'All three pastel hues must appear')

    def test_overcast_suppresses_the_sheet(self):
        clear = self.image(-0.10, overcast=0.0)
        cloudy = self.image(-0.10, overcast=1.0)
        self.assertGreater(self.peak(clear), 0.008)
        self.assertLess(self.peak(cloudy), 1e-7)

    def test_winter_strengthens_the_sheet(self):
        winter = self.peak(self.image(-0.10, winter=1.0))
        summer = self.peak(self.image(-0.10, winter=0.0))
        self.assertGreater(winter, summer * 2.0)

    def test_layer_stays_low_and_structured(self):
        image = self.image(-0.10)
        self.assertGreater(self.peak(image, LOW), 0.008)
        self.assertLess(self.peak(image, TOP), 1e-6,
                        'No haze above the top of the sheet')
        active = image.max(axis=2)[image.max(axis=2) > 0.002]
        self.assertGreater(float(active.std()), float(active.mean()) * 0.18,
                           'Sheets must not be a uniform wash')


if __name__ == '__main__':
    unittest.main()
