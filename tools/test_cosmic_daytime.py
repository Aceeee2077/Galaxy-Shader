"""GPU checks for the daytime cosmic-sky early-out.

Every cosmic layer is scaled by cosmicNight, which is exactly zero once the sun
is up. The shader now skips the whole block instead of evaluating galaxy,
aurora, meteor and comet noise and multiplying the result by zero. These tests
render the sky with the gate, with the gate removed, and with the cosmic layer
switched off, and require the gated image to match both the previous behaviour
and the layer-free image by day.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 256
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def sky_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/atmosphere.glsl') +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    // Cover the visible dome, stopping just below the horizon so the analytic
    // below-horizon extension does not dominate the comparison.
    vec3 ray = normalize(vec3(uv.x, uv.y * 0.75 + 0.02, 1.4));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}''')


def gated_source():
    return sky_source()


def ungated_source():
    # The exact pre-change code: same block, no branch.
    return sky_source().replace('if (cosmicNight > 0.002) {', '{')


def cosmic_off_source():
    return sky_source().replace('#define COSMIC_SKY_QUALITY 2',
                               '#define COSMIC_SKY_QUALITY 0')


class CosmicDaytimeRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.gated = cls.renderer.gl.compile(VERTEX, gated_source())
        cls.ungated = cls.renderer.gl.compile(VERTEX, ungated_source())
        cls.cosmic_off = cls.renderer.gl.compile(VERTEX, cosmic_off_source())

    @classmethod
    def tearDownClass(cls):
        for program in (cls.gated, cls.ungated, cls.cosmic_off):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, elevation_degrees):
        elevation = np.radians(elevation_degrees)
        sun = np.array([0.0, np.sin(elevation), np.cos(elevation)], np.float32)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'sunPosition', sun * 100.0)
        cls.renderer.uniform(program, 'moonPosition', -sun * 100.0)
        cls.renderer.full_screen()
        cls.renderer.check('cosmic daytime sky')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_noon_matches_cosmic_off(self):
        gated = self.image(self.gated, 80.0)
        off = self.image(self.cosmic_off, 80.0)
        np.testing.assert_array_equal(
            gated, off, 'A daytime sky must not contain any cosmic energy')

    def test_noon_matches_previous_code(self):
        gated = self.image(self.gated, 80.0)
        ungated = self.image(self.ungated, 80.0)
        np.testing.assert_array_equal(
            gated, ungated, 'The early-out must not change the noon sky')

    def test_night_matches_previous_code(self):
        gated = self.image(self.gated, -25.0)
        ungated = self.image(self.ungated, -25.0)
        np.testing.assert_array_equal(
            gated, ungated, 'The night sky must keep every cosmic layer')

    def test_twilight_matches_previous_code(self):
        gated = self.image(self.gated, -2.0)
        ungated = self.image(self.ungated, -2.0)
        np.testing.assert_array_equal(
            gated, ungated, 'The gate must stay open through twilight')

    def test_night_keeps_visible_cosmic_energy(self):
        gated = self.image(self.gated, -25.0)
        off = self.image(self.cosmic_off, -25.0)
        delta = np.abs(gated - off).max()
        self.assertGreater(delta, 1e-4,
                           'The cosmic layer must remain visible at night')


if __name__ == '__main__':
    unittest.main()
