"""GPU checks for the eclipse-only gate in the sun-disk block.

The fixture calls `atmosphere` directly over a sky ring, once on an ordinary
day and once on the eclipse day. It is an engineering check, not a Minecraft
screenshot. Probes count the eclipse aureole exponential.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '        if (eclipse > 0.0) {'
GATE_OLD = '        if (eclipse >= 0.0) {'
ECLIPSE_EXP = 'exp(-pow((1.0-mu)*58.0,2.0))'


def shader_source(probe=False, old=False, eclipse_day=False):
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float eclipseCalls=0.0;\n')
    if probe:
        head += 'float probeEclipseExp(float x);\n'
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert GATE_NEW in core and ECLIPSE_EXP in core
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    if eclipse_day:
        assert '#define SEASON_MODE 0' in core
        core = core.replace('#define SEASON_MODE 0', '#define SEASON_MODE 2')
    if probe:
        core = core.replace(ECLIPSE_EXP, 'probeEclipseExp((1.0-mu)*58.0)')
        core += '''
float probeEclipseExp(float x){eclipseCalls+=1.0;return exp(-x*x);}
'''
    counts = 'eclipseCalls' if probe else '1.0'
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


class EclipseGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))
        cls.new_eclipse = cls.renderer.gl.compile(
            VERTEX, shader_source(eclipse_day=True))
        cls.old_eclipse = cls.renderer.gl.compile(
            VERTEX, shader_source(old=True, eclipse_day=True))
        cls.new_probe = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True))
        cls.old_probe = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True, old=True))
        cls.new_probe_eclipse = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True, eclipse_day=True))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_eclipse, cls.old_eclipse,
                        cls.new_probe, cls.old_probe, cls.new_probe_eclipse):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, time=6000):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(20.0)
        direction = [float(np.cos(elevation)) * 300.0,
                     float(np.sin(elevation)) * 300.0, 0.0]
        cls.renderer.uniform(program, 'sunPosition', direction)
        cls.renderer.uniform(program, 'shadowLightPosition', direction)
        cls.renderer.uniform(program, 'moonPosition', [-v for v in direction])
        cls.renderer.uniform(program, 'worldTime', time)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', 0.0)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', 0.0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('eclipse gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_ordinary_day_matches_the_previous_build(self):
        new = self.image(self.new)
        old = self.image(self.old)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_eclipse_day_matches_the_previous_build(self):
        new = self.image(self.new_eclipse)
        old = self.image(self.old_eclipse)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_ordinary_day_skips_the_aureole_exponential(self):
        new = self.image(self.new_probe)
        old = self.image(self.old_probe)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_eclipse_day_still_evaluates_the_aureole(self):
        new = self.image(self.new_probe_eclipse)
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_deterministic(self):
        a = self.image(self.new_eclipse)
        b = self.image(self.new_eclipse)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
