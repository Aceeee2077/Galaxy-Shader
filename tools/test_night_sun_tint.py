"""GPU checks for skipping the sunlight tint on the night sky.

The fixture calls `atmosphere` directly over a sky dome at four sun heights.
It is an engineering check, not a Minecraft screenshot. The probe counts calls
to `sunlightColor` made by the atmosphere entry point itself.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
TINT_NEW = 'vec3 sunTint = day > 0.0 ? sunlightColor() : vec3(0.0);'
TINT_OLD = 'vec3 sunTint = sunlightColor();'
PROBE_NEW = 'vec3 sunTint = day > 0.0 ? probeSunTint() : vec3(0.0);'
PROBE_OLD = 'vec3 sunTint = probeSunTint();'


def shader_source(probe=False, old=False):
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tintCalls=0.0;\n')
    if probe:
        head += 'vec3 probeSunTint();\n'
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert TINT_NEW in core
    if probe:
        core = core.replace(TINT_NEW, PROBE_OLD if old else PROBE_NEW)
        core += '''
vec3 probeSunTint(){tintCalls+=1.0;return sunlightColor();}
'''
    elif old:
        core = core.replace(TINT_NEW, TINT_OLD)
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


class NightSunTint(unittest.TestCase):
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
        cls.renderer.check('night sun tint')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_night_matches_the_previous_build(self):
        new = self.image(self.new, -30.0)
        old = self.image(self.old, -30.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_moonlit_night_matches(self):
        new = self.image(self.new, -12.0)
        old = self.image(self.old, -12.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_twilight_matches(self):
        new = self.image(self.new, 0.0)
        old = self.image(self.old, 0.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_noon_matches(self):
        new = self.image(self.new, 35.0)
        old = self.image(self.old, 35.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_night_skips_the_sun_tint(self):
        new = self.image(self.new_probe, -30.0)
        old = self.image(self.old_probe, -30.0)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_daytime_still_evaluates_the_sun_tint(self):
        for elevation in (0.0, 35.0):
            new = self.image(self.new_probe, elevation)
            self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_deterministic(self):
        a = self.image(self.new, -20.0)
        b = self.image(self.new, -20.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
