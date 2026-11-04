"""GPU checks for the early exit of the lunar halo companions.

The fixture samples `iceHalo` inside the 37-degree cap where the halo costs
anything at all. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
LUNAR_GATE = 'if (pillarGate > 0.0 || lunarDogGate > 0.0) {'
ALWAYS = 'if (pillarGate > -1.0) {'
HALO_ATAN = 'atan(dot('


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float haloAtan=0.0;\nfloat probeAtan(float y, float x);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
uniform float testLunar;
float probeAtan(float y, float x){haloAtan+=1.0;return atan(y,x);}
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 light = normalize(testSun);
    vec3 up = abs(light.y) > 0.95 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 u = normalize(cross(up, light));
    vec3 w = cross(light, u);
    float theta = radians(35.5 * uv.y);
    float phi = 6.2831853 * uv.x;
    vec3 ray = normalize(cos(theta) * light +
                         sin(theta) * (cos(phi) * u + sin(phi) * w));
    vec3 colour = iceHalo(ray, light, testVisibility, vec3(1.0),
                          testLunar);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


class LunarCompanionGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = source('haloAtan')
        assert LUNAR_GATE in base
        old = base.replace(LUNAR_GATE, ALWAYS)
        cls.new = cls.renderer.gl.compile(VERTEX, base)
        cls.old = cls.renderer.gl.compile(VERTEX, old)
        cls.new_probe = cls.renderer.gl.compile(
            VERTEX, base.replace(HALO_ATAN, 'probeAtan(dot('))
        cls.old_probe = cls.renderer.gl.compile(
            VERTEX, old.replace(HALO_ATAN, 'probeAtan(dot('))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_probe, cls.old_probe):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_deg, lunar=1.0, visibility=1.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testVisibility', float(visibility))
        cls.renderer.uniform(program, 'testLunar', float(lunar))
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(sun_deg)) * np.cos(0.6),
                              np.sin(np.deg2rad(sun_deg)),
                              np.cos(np.deg2rad(sun_deg)) * np.sin(0.6)])
        cls.renderer.full_screen()
        cls.renderer.check('lunar companion gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_gates_match_the_previous_moon_halo(self):
        for sun, lunar in ((3.0, 1.0), (10.0, 1.0), (20.0, 1.0),
                           (30.0, 1.0), (50.0, 1.0), (70.0, 1.0),
                           (10.0, 0.0), (50.0, 0.0)):
            new = self.image(self.new, sun, lunar)
            old = self.image(self.old, sun, lunar)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3],
                                       atol=2e-4)

    def test_high_moon_skips_the_companions(self):
        new = float(self.image(self.new_probe, 50.0)[:, :, 3].sum())
        old = float(self.image(self.old_probe, 50.0)[:, :, 3].sum())
        self.assertEqual(new, 0.0)
        self.assertGreater(old, 0.0)

    def test_low_moon_still_runs_the_dogs(self):
        new = self.image(self.new_probe, 10.0)
        old = self.image(self.old_probe, 10.0)
        self.assertEqual(float(new[:, :, 3].sum()), float(old[:, :, 3].sum()))
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_moon_dogs_are_still_visible(self):
        self.assertGreater(
            float(self.image(self.new, 10.0)[:, :, :3].max()), 1e-4)

    def test_zero_visibility_returns_black(self):
        image = self.image(self.new, 10.0, 1.0, 0.0)
        self.assertEqual(float(image[:, :, :3].max()), 0.0)

    def test_deterministic(self):
        a = self.image(self.new, 10.0)
        b = self.image(self.new, 10.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
