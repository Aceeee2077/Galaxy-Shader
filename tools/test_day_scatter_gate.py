"""GPU checks for the night skip of the daytime scattering block.

The fixture calls `atmosphere` directly over a sky dome at four sun heights.
It is an engineering check, not a Minecraft screenshot. The probe counts calls
to the fixed horizon tint, which only the daytime block evaluates.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '    if (day > 0.0) {'
GATE_OLD = '    if (day >= 0.0) {'
TINT_CALL = 'vec3 warmBand=horizonSunTint()*0.46'


def shader_source(probe=False, old=False):
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tintCalls=0.0;\n')
    if probe:
        head += 'vec3 probeHorizonTint();\n'
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert core.count(GATE_NEW) == 1 and TINT_CALL in core
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    if probe:
        core = core.replace(TINT_CALL, 'vec3 warmBand=probeHorizonTint()*0.46')
        core += '''
vec3 probeHorizonTint(){tintCalls+=1.0;return horizonSunTint();}
'''
    counts = 'tintCalls' if probe else '1.0'
    return (head + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 60.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = atmosphere(ray, true);
    gl_FragColor = vec4(colour, ''' + counts + ''');
}''')


class NightScatterGate(unittest.TestCase):
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
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        angle = np.deg2rad(elevation)
        direction = [float(np.cos(angle)) * 300.0,
                     float(np.sin(angle)) * 300.0, 0.0]
        cls.renderer.uniform(program, 'sunPosition', direction)
        cls.renderer.uniform(program, 'shadowLightPosition', direction)
        cls.renderer.uniform(program, 'moonPosition', [-v for v in direction])
        cls.renderer.uniform(program, 'worldTime', 6000)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', 0.0)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', 0.0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('day scatter gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_night_matches_the_previous_build(self):
        new = self.image(self.new, -30.0)
        old = self.image(self.old, -30.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_just_below_the_cutoff_matches(self):
        new = self.image(self.new, -6.0)
        old = self.image(self.old, -6.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_sunrise_matches(self):
        new = self.image(self.new, 0.0)
        old = self.image(self.old, 0.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_noon_matches(self):
        new = self.image(self.new, 35.0)
        old = self.image(self.old, 35.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_night_skips_the_daytime_block(self):
        new = self.image(self.new_probe, -30.0)
        old = self.image(self.old_probe, -30.0)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_daytime_still_evaluates_the_block(self):
        for elevation in (0.0, 35.0):
            new = self.image(self.new_probe, elevation)
            self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_deterministic(self):
        a = self.image(self.new, -15.0)
        b = self.image(self.new, -15.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
