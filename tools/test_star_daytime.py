"""GPU checks for the daytime star-field early-out.

The star layer is multiplied by (1 - day) * (1 - overcast), which is exactly
zero at noon. The shader now skips the cell hash, scintillation and colour
hashes in that case. The gated sky must match the previous code at noon and at
night, and must still contain visible stars at night.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 256
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DISABLED = ('float starBrightness = star*twinkle*0.7*(1.0-day)*(1.0-overcast)*')


def sky_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/atmosphere.glsl') +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 ray = normalize(vec3(uv.x, uv.y * 0.75 + 0.02, 1.4));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}''')


def gated_source():
    return sky_source()


def ungated_source():
    return sky_source().replace('if ((1.0-day)*(1.0-overcast) > 0.002) {', '{')


def starless_source():
    return sky_source().replace(
        DISABLED, 'float starBrightness = 0.0*(1.0-day)*(1.0-overcast)*')


class StarDaytimeRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.gated = cls.renderer.gl.compile(VERTEX, gated_source())
        cls.ungated = cls.renderer.gl.compile(VERTEX, ungated_source())
        cls.starless = cls.renderer.gl.compile(VERTEX, starless_source())

    @classmethod
    def tearDownClass(cls):
        for program in (cls.gated, cls.ungated, cls.starless):
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
        cls.renderer.check('star daytime sky')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_noon_matches_previous_code(self):
        np.testing.assert_array_equal(
            self.image(self.gated, 80.0), self.image(self.ungated, 80.0),
            'The daytime star gate must not change a single pixel')

    def test_noon_has_no_star_energy(self):
        np.testing.assert_array_equal(
            self.image(self.gated, 80.0), self.image(self.starless, 80.0),
            'A noon sky must not contain star energy')

    def test_night_matches_previous_code(self):
        np.testing.assert_array_equal(
            self.image(self.gated, -25.0), self.image(self.ungated, -25.0),
            'The night sky must keep the previous star field')

    def test_night_keeps_visible_stars(self):
        delta = np.abs(self.image(self.gated, -25.0) -
                       self.image(self.starless, -25.0)).max()
        self.assertGreater(delta, 1e-3, 'Stars must remain visible at night')


if __name__ == '__main__':
    unittest.main()
