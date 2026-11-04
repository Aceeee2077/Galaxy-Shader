"""GPU checks for the vertical bound on the parhelic circle.

The fixture samples `iceHaloCompanions` over the upper sky. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE = 'if (sun.y > 0.02 && abs(ray.y - sun.y) < 0.15) {'
OLD_GATE = 'if (sun.y > 0.02) {'
BAND_EXP = '        float height = exp(-pow((ray.y - sun.y) / 0.009, 2.0));'


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float parhelicExp=0.0;\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo_extras.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(1.0 + 84.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = iceHaloCompanions(ray, normalize(testSun), testVisibility);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def instrument(text):
    return text.replace(BAND_EXP,
                        '        parhelicExp+=1.0;\n' + BAND_EXP)


class ParhelicGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = source('parhelicExp')
        assert GATE in base and BAND_EXP in base
        old = base.replace(GATE, OLD_GATE)
        cls.new = cls.renderer.gl.compile(VERTEX, base)
        cls.old = cls.renderer.gl.compile(VERTEX, old)
        cls.new_probe = cls.renderer.gl.compile(VERTEX, instrument(base))
        cls.old_probe = cls.renderer.gl.compile(VERTEX, instrument(old))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_probe, cls.old_probe):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_deg, visibility=1.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testVisibility', float(visibility))
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(sun_deg)),
                              np.sin(np.deg2rad(sun_deg)), 0.0])
        cls.renderer.full_screen()
        cls.renderer.check('parhelic gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_gates_match_the_previous_band(self):
        for sun in (5.0, 20.0, 40.0, 60.0, 89.0):
            new = self.image(self.new, sun)
            old = self.image(self.old, sun)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3],
                                       atol=2e-4)

    def test_pixels_away_from_the_band_skip_the_exp(self):
        new = float(self.image(self.new_probe, 20.0)[:, :, 3].sum())
        old = float(self.image(self.old_probe, 20.0)[:, :, 3].sum())
        self.assertLess(new, old * 0.5)

    def test_band_is_still_visible(self):
        self.assertGreater(
            float(self.image(self.new, 20.0)[:, :, :3].max()), 1e-4)

    def test_zero_visibility_returns_black(self):
        image = self.image(self.new, 20.0, 0.0)
        self.assertEqual(float(image[:, :, :3].max()), 0.0)

    def test_deterministic(self):
        a = self.image(self.new, 20.0)
        b = self.image(self.new, 20.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
