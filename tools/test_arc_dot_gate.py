"""GPU checks for the azimuth dot gates on the circumzenithal and Parry arcs.

The fixture samples `iceHaloCompanions` over a full sky. It is an engineering
check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
CZA_GATE = 'azimuth > 0.48'
PARRY_GATE = 'azimuth > 0.865'
ALWAYS = 'azimuth > -2.0'
ARC_ACOS = 'acos(clamp(azimuth, -1.0, 1.0))'


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float arcCalls=0.0;\nfloat probeAcos(float x);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo_extras.glsl') +
            '''
float probeAcos(float x){arcCalls+=1.0;return acos(x);}
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(2.0 + 86.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = iceHaloCompanions(ray, normalize(testSun), 1.0);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


class ArcDotGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = source('arcCalls')
        assert CZA_GATE in base and PARRY_GATE in base
        old = base.replace(CZA_GATE, ALWAYS).replace(PARRY_GATE, ALWAYS)
        cls.new = cls.renderer.gl.compile(VERTEX, base)
        cls.old = cls.renderer.gl.compile(VERTEX, old)
        cls.new_probe = cls.renderer.gl.compile(
            VERTEX, base.replace(ARC_ACOS, 'probeAcos(clamp(azimuth, -1.0, 1.0))'))
        cls.old_probe = cls.renderer.gl.compile(
            VERTEX, old.replace(ARC_ACOS,
                                'probeAcos(clamp(azimuth, -1.0, 1.0))'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_probe, cls.old_probe):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_deg):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(sun_deg)),
                              np.sin(np.deg2rad(sun_deg)), 0.0])
        cls.renderer.full_screen()
        cls.renderer.check('arc dot gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_gates_match_the_previous_arcs(self):
        for sun in (5.0, 20.0, 30.0, 70.0):
            new = self.image(self.new, sun)
            old = self.image(self.old, sun)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_circumzenithal_arc_is_still_visible(self):
        image = self.image(self.new, 20.0)
        self.assertGreater(float(image[:, :, :3].max()), 1e-4)

    def test_outside_cone_pixels_skip_the_acos(self):
        new = self.image(self.new_probe, 20.0)
        old = self.image(self.old_probe, 20.0)
        self.assertGreater(float(old[:, :, 3].sum()), float(new[:, :, 3].sum()))
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_deterministic(self):
        a = self.image(self.new, 20.0)
        b = self.image(self.new, 20.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
