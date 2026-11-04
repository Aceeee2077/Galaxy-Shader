"""GPU checks for the angular gate around the solar aureole.

The fixture calls `atmosphere` directly over a full azimuth ring. It is an
engineering check, not a Minecraft screenshot. Probes count the two vector
exponentials, which the RGB output alone cannot show.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 360, 90
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '    if (solarAngle < diskEdge + 0.21) {'
GATE_OLD = '    if (solarAngle >= 0.0) {'


def shader_source(probe=False, old=False, disks='false'):
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tightCalls=0.0;\nfloat wideCalls=0.0;\n')
    if probe:
        head += 'vec3 probeTight(vec3 x);\nvec3 probeWide(vec3 x);\n'
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert GATE_NEW in core
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    if probe:
        core = (core.replace('exp(-haloDistance*vec3(1400.0,1800.0,2400.0))',
                             'probeTight(-haloDistance*vec3(1400.0,1800.0,2400.0))')
                    .replace('exp(-haloDistance*vec3(560.0,500.0,440.0))',
                             'probeWide(-haloDistance*vec3(560.0,500.0,440.0))'))
        core += '''
vec3 probeTight(vec3 x){tightCalls+=1.0;return exp(x);}
vec3 probeWide(vec3 x){wideCalls+=1.0;return exp(x);}
'''
    counts = 'tightCalls*2.0+wideCalls' if probe else '1.0'
    return (head + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 55.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = atmosphere(ray, ''' + disks + ''');
    gl_FragColor = vec4(colour, ''' + counts + ''');
}''')


class SolarAureoleGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))
        cls.new_probe = cls.renderer.gl.compile(VERTEX, shader_source(probe=True))
        cls.old_probe = cls.renderer.gl.compile(
            VERTEX, shader_source(probe=True, old=True))
        cls.new_disks = cls.renderer.gl.compile(
            VERTEX, shader_source(disks='true'))
        cls.old_disks = cls.renderer.gl.compile(
            VERTEX, shader_source(old=True, disks='true'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.new_probe, cls.old_probe,
                        cls.new_disks, cls.old_disks):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_degrees=20.0, time=6000):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(sun_degrees)
        cls.renderer.uniform(program, 'sunPosition',
                             [float(np.cos(elevation)) * 300.0,
                              float(np.sin(elevation)) * 300.0, 0.0])
        cls.renderer.uniform(program, 'shadowLightPosition',
                             [float(np.cos(elevation)) * 300.0,
                              float(np.sin(elevation)) * 300.0, 0.0])
        cls.renderer.uniform(program, 'moonPosition',
                             [-float(np.cos(elevation)) * 300.0,
                              -float(np.sin(elevation)) * 300.0, 0.0])
        cls.renderer.uniform(program, 'worldTime', time)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', 0.0)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', 0.0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('aureole gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_sky_output_matches_the_previous_build(self):
        for sun in (5.0, 20.0, 45.0, 89.0):
            new = self.image(self.new, sun)
            old = self.image(self.old, sun)
            np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_sky_with_disks_matches_the_previous_build(self):
        new = self.image(self.new_disks, 20.0)
        old = self.image(self.old_disks, 20.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_distant_sky_skips_both_exponentials(self):
        new = self.image(self.new_probe, 20.0)
        old = self.image(self.old_probe, 20.0)
        skipped = int(np.count_nonzero(new[:, :, 3] == 0.0))
        self.assertGreater(skipped, int(W * H * 0.75))
        self.assertLess(float(new[:, :, 3].sum()), float(old[:, :, 3].sum()))
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_pixels_near_the_sun_still_evaluate_the_aureole(self):
        new = self.image(self.new_probe, 20.0)
        self.assertEqual(float(new[:, :, 3].max()), 3.0)
        self.assertGreater(int(np.count_nonzero(new[:, :, 3] == 3.0)), 10)

    def test_deterministic(self):
        a = self.image(self.new, 20.0)
        b = self.image(self.new, 20.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
