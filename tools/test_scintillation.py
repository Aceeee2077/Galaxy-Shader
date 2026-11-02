"""GPU checks for stellar scintillation.

The fixture evaluates the authored brightness factor directly for many star
seeds and altitudes. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 128, 64
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


class ScintillationRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/scintillation.glsl') +
                    '''
uniform vec2 testResolution;
uniform float testSeed;
uniform float testAltitude;
uniform float testTime;
uniform float testAmount;
void main() {
    gl_FragColor = vec4(starScintillation(testSeed, testAltitude,
                                          testTime, testAmount));
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
    def value(cls, seed, altitude, time, amount=1.0):
        cls.renderer.uniform(cls.program, 'testSeed', float(seed))
        cls.renderer.uniform(cls.program, 'testAltitude', float(altitude))
        cls.renderer.uniform(cls.program, 'testTime', float(time))
        cls.renderer.uniform(cls.program, 'testAmount', float(amount))
        cls.renderer.full_screen()
        cls.renderer.check('star scintillation')
        return float(cls.renderer.read(W, H)[0, 0, 0])

    def curve(self, seed, altitude, amount=1.0):
        times = np.linspace(0.0, 1.5, 90)
        return np.array([self.value(seed, altitude, t, amount) for t in times])

    def test_deterministic(self):
        self.assertEqual(self.value(0.37, 0.3, 1.25),
                         self.value(0.37, 0.3, 1.25))

    def test_neutral_when_disabled(self):
        for time in [0.0, 0.31, 1.27]:
            self.assertAlmostEqual(self.value(0.51, 0.2, time, 0.0), 1.0, places=6)

    def test_stars_modulate_over_time(self):
        value = self.curve(0.24, 0.35)
        self.assertGreater(float(value.std()), 0.12, 'Brightness must flicker')
        self.assertGreater(float(value.max() - value.min()), 0.45)
        self.assertTrue(np.isfinite(value).all())

    def test_horizon_scintillates_more_than_zenith(self):
        low = self.curve(0.63, 0.03)
        high = self.curve(0.63, 1.20)
        self.assertGreater(float(low.max() - low.min()),
                           float(high.max() - high.min()) * 1.6,
                           'Lower sight lines cross more turbulent air')

    def test_amplitude_scales_with_the_slider(self):
        soft = self.curve(0.18, 0.25, 0.5)
        full = self.curve(0.18, 0.25, 1.5)
        self.assertGreater(float(full.max() - full.min()),
                           float(soft.max() - soft.min()) * 1.8)

    def test_brightness_stays_bounded(self):
        for seed in np.linspace(0.0, 1.0, 9):
            curve = self.curve(float(seed), 0.01, 2.0)
            self.assertGreaterEqual(float(curve.min()), 0.07)
            self.assertLessEqual(float(curve.max()), 3.2)


if __name__ == '__main__':
    unittest.main()
