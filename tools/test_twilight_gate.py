"""GPU checks for the twilight-optics gate early-outs.

The fixture samples `twilightOptics` over a full sky. It is an engineering
check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
BELT_GATE = '''    // Both smoothsteps clamp outside the twilight window, so the gate is a
    // hard zero for most of the day. Nothing below survives the multiply.
    if (gate <= 0.0) return vec3(0.0);
'''
ZODIAC_GATE = '''    // Outside the twilight window the cone is multiplied by zero, so skip the
    // normalise/acos/exp chain that only exists to shape an invisible cone.
    if (gate <= 0.0) return vec3(0.0);
'''
AIR_GATE = '''    // Daytime airglow is entirely gone; skip the two noise lookups and the
    // cosine ripples that would be multiplied away.
    if (night <= 0.0) return vec3(0.0);
'''
CLEAR_GATE = '''    // A fully overcast sky scales every term by zero; skip the three calls.
    if (clear <= 0.0) return vec3(0.0);
'''
COUNTERS = ('float beltWork=0.0;\nfloat zodiacWork=0.0;\n'
            'float airWork=0.0;\n')


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            COUNTERS + expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/twilight_optics.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(0.5 + 80.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = twilightOptics(ray, normalize(testSun), testOvercast);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def instrument(text):
    """Count how often each twilight body reaches its expensive chain."""
    text = text.replace('    float arc = antiSolarArc(ray, sun);',
                        '    beltWork+=1.0;\n    float arc = antiSolarArc(ray, sun);')
    text = text.replace('    float cone = exp(',
                        '    zodiacWork+=1.0;\n    float cone = exp(')
    text = text.replace('    float layer = exp(',
                        '    airWork+=1.0;\n    float layer = exp(')
    return text


class TwilightGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        probe = 'beltWork*100.0 + zodiacWork*10.0 + airWork'
        plain = source(probe)
        for gate in (BELT_GATE, ZODIAC_GATE, AIR_GATE, CLEAR_GATE):
            assert gate in plain, gate
        old = plain
        for gate in (BELT_GATE, ZODIAC_GATE, AIR_GATE, CLEAR_GATE):
            old = old.replace(gate, '')
        cls.new = cls.renderer.gl.compile(VERTEX, instrument(plain))
        cls.old = cls.renderer.gl.compile(VERTEX, instrument(old))
        cls.new_probe = cls.new
        cls.old_probe = cls.old

    @classmethod
    def tearDownClass(cls):
        for program in {cls.new, cls.old}:
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_deg, overcast=0.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'frameTimeCounter', 7.0)
        cls.renderer.uniform(program, 'testOvercast', float(overcast))
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(sun_deg)),
                              np.sin(np.deg2rad(sun_deg)), 0.0])
        cls.renderer.full_screen()
        cls.renderer.check('twilight gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_gates_match_the_previous_sky(self):
        for sun, overcast in ((60.0, 0.0), (2.0, 0.0), (-10.0, 0.0),
                              (-35.0, 0.0), (-35.0, 0.6), (-10.0, 1.0)):
            new = self.image(self.new, sun, overcast)
            old = self.image(self.old, sun, overcast)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3],
                                       atol=2e-4)

    def test_daytime_skips_the_twilight_bodies(self):
        new = float(self.image(self.new_probe, 60.0)[:, :, 3].sum())
        old = float(self.image(self.old_probe, 60.0)[:, :, 3].sum())
        self.assertEqual(new, 0.0)
        self.assertGreater(old, 0.0)

    def test_twilight_still_runs_the_bodies(self):
        new = self.image(self.new_probe, -10.0)
        old = self.image(self.old_probe, -10.0)
        self.assertGreater(float(new[:, :, 3].sum()), 0.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_full_overcast_skips_every_body(self):
        new = float(self.image(self.new_probe, -10.0, 1.0)[:, :, 3].sum())
        old = float(self.image(self.old_probe, -10.0, 1.0)[:, :, 3].sum())
        self.assertEqual(new, 0.0)
        self.assertGreater(old, 0.0)

    def test_twilight_sky_is_visible(self):
        image = self.image(self.new, -10.0)
        self.assertGreater(float(image[:, :, :3].max()), 1e-4)

    def test_deterministic(self):
        a = self.image(self.new, -10.0)
        b = self.image(self.new, -10.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
