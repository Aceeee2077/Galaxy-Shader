"""GPU checks for the twilight gate on the sunward sky fill.

The probe counts calls to `sunlightColor` inside the real `skyIrradiance` over a
hemisphere of normals. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 120, 60
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '''    float twilightSun=lowSun*day;
    if (twilightSun>0.0)
        upper+=sunlightColor()*twilightSun*sunward*(1.0-overcast)*0.025;'''
GATE_OLD = '    upper+=sunlightColor()*lowSun*day*sunward*(1.0-overcast)*0.025;'
DEFINITION = 'vec3 sunlightColor() {'
RENAMED = 'vec3 sunlightCore() {'
WRAPPER = '''
vec3 sunlightColor(){
    tintCalls+=1.0;
    return sunlightCore();
}
'''
DOMAIN = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(90.0 * uv.y);
    vec3 n = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(skyIrradiance(n), tintCalls);
}'''


def shader_source(probe=False, old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert core.count(GATE_NEW) == 1
    assert core.count(DEFINITION) == 1
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    head = '#version 330 compatibility\n#define DIMENSION 0\n'
    if probe:
        core = core.replace(DEFINITION, RENAMED)
        head += ('float tintCalls=0.0;\nvec3 sunlightColor();\n')
        core += WRAPPER
    counts = 'tintCalls' if probe else '1.0'
    return head + core + DOMAIN.replace('tintCalls', counts)


class SkyIrradianceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))
        cls.new_probe = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True))
        cls.old_probe = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True, old=True))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_probe, cls.old_probe):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, elevation):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        angle = np.deg2rad(elevation)
        direction = [float(np.cos(angle)) * 300.0,
                     float(np.sin(angle)) * 300.0, 0.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('sky irradiance gate')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_high_sun_skips_the_tint(self):
        for elevation in (45.0, 80.0):
            new = self.image(self.new_probe, elevation)
            old = self.image(self.old_probe, elevation)
            self.assertEqual(float(new[:, :, 3].sum()), 0.0)
            self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_deep_night_skips_the_tint(self):
        new = self.image(self.new_probe, -30.0)
        old = self.image(self.old_probe, -30.0)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_twilight_still_evaluates_the_tint(self):
        for elevation in (0.0, 10.0):
            new = self.image(self.new_probe, elevation)
            self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_output_is_unchanged(self):
        for elevation in (-30.0, 0.0, 10.0, 45.0, 80.0):
            new = self.image(self.new, elevation)
            old = self.image(self.old, elevation)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4,
                                       err_msg=f'sun at {elevation} degrees')

    def test_deterministic(self):
        a = self.image(self.new, 45.0)
        b = self.image(self.new, 45.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
