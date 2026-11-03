"""GPU checks for two exact cloud-march savings.

The fixture calls `volumetricClouds` directly with a fixed sky. It is an
engineering check, not a Minecraft screenshot. Probe variants count the calls
the optimised code skips, which the RGB output alone cannot show.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
AIR_NEW = '''    vec3 airColor=vec3(0.0);
    bool airReady=false;'''
AIR_OLD = '    vec3 airColor=atmosphere(ray,false);'
AIR_CALL = '        if (!airReady) { airColor=atmosphere(ray,false); airReady=true; }'
EROSION_NEW = '''    float erosion=0.05*(1.0-shape);
    if(detail>0.5 && !lightSample && shape>0.0)
        erosion=volumeNoise(q*8.1)*0.10*(1.0-shape);'''
EROSION_OLD = '''    float erosion;
    if(detail>0.5 && !lightSample) erosion=volumeNoise(q*8.1)*0.10;
    else erosion=0.05;
    erosion*=1.0-shape;'''


def shader_source(probe='probeCount'):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float probeCount=0.0;\nfloat erosionCalls=0.0;\n'
            'vec3 probeAtmosphere(vec3 ray,bool disks);\n'
            'float probeErosion(vec3 p);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/clouds.glsl') +
            '''
vec3 probeAtmosphere(vec3 ray,bool disks){probeCount+=1.0;return atmosphere(ray,disks);}
float probeErosion(vec3 p){erosionCalls+=1.0;return volumeNoise(p);}
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 40.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = volumetricClouds(vec3(0.10, 0.16, 0.26), ray,
                                   vec3(0.0, 70.0, 0.0), false);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


class CloudMarchSaving(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = shader_source()
        assert AIR_NEW in base and AIR_CALL in base and EROSION_NEW in base
        cls.new = cls.renderer.gl.compile(VERTEX, base)
        old = base.replace(AIR_NEW, AIR_OLD).replace(AIR_CALL + '\n', '')
        old = old.replace(EROSION_NEW, EROSION_OLD)
        cls.old = cls.renderer.gl.compile(VERTEX, old)
        cls.air_probe = cls.renderer.gl.compile(
            VERTEX, base.replace('atmosphere(ray,false)',
                                 'probeAtmosphere(ray,false)'))
        # The lowest cloud-coverage option leaves more sky without a hit, so
        # the probe finds skips without relying on a single stray pixel.
        low = base.replace('#define CLOUD_COVERAGE 0.45',
                           '#define CLOUD_COVERAGE 0.25')
        cls.plain_low = cls.renderer.gl.compile(VERTEX, low)
        cls.air_probe_low = cls.renderer.gl.compile(
            VERTEX, low.replace('atmosphere(ray,false)',
                                'probeAtmosphere(ray,false)'))
        erosion_base = shader_source('erosionCalls')
        cls.erosion_probe = cls.renderer.gl.compile(
            VERTEX, erosion_base.replace('volumeNoise(q*8.1)',
                                         'probeErosion(q*8.1)'))
        cls.old_erosion_probe = cls.renderer.gl.compile(
            VERTEX, erosion_base.replace(AIR_NEW, AIR_OLD)
            .replace(AIR_CALL + '\n', '')
            .replace(EROSION_NEW, EROSION_OLD)
            .replace('volumeNoise(q*8.1)', 'probeErosion(q*8.1)'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.air_probe, cls.plain_low,
                        cls.air_probe_low, cls.erosion_probe,
                        cls.old_erosion_probe):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, weather=(0.0, 0.0, 0.0), time=6000):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'sunPosition', [0.0, 300.0, 0.0])
        cls.renderer.uniform(program, 'shadowLightPosition', [0.0, 300.0, 0.0])
        cls.renderer.uniform(program, 'moonPosition', [0.0, -300.0, 0.0])
        cls.renderer.uniform(program, 'worldTime', time)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', weather[0])
        cls.renderer.uniform(program, 'wetness', weather[1])
        cls.renderer.uniform(program, 'thunderStrength', weather[2])
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('cloud march saving')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_lazy_air_sample_matches_eager_on_clear_sky(self):
        new = self.image(self.new)
        old = self.image(self.old)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_lazy_air_sample_matches_eager_in_rain(self):
        new = self.image(self.new, weather=(1.0, 1.0, 0.0))
        old = self.image(self.old, weather=(1.0, 1.0, 0.0))
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_lazy_air_sample_matches_eager_at_dusk(self):
        new = self.image(self.new, time=13000)
        old = self.image(self.old, time=13000)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_erosion_matches_the_previous_clouds(self):
        new = self.image(self.new)
        old = self.image(self.old)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_clear_rays_skip_the_atmosphere_sample(self):
        probed = self.image(self.air_probe_low)
        misses = int(np.count_nonzero(probed[:, :, 3] == 0.0))
        self.assertGreater(misses, 10)
        plain = self.image(self.plain_low)
        np.testing.assert_allclose(probed[:, :, :3], plain[:, :, :3], atol=2e-4)

    def test_empty_samples_skip_the_erosion_noise(self):
        new = self.image(self.erosion_probe)
        old = self.image(self.old_erosion_probe)
        new_calls = float(new[:, :, 3].sum())
        old_calls = float(old[:, :, 3].sum())
        self.assertGreater(old_calls, new_calls)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_deterministic(self):
        a = self.image(self.new)
        b = self.image(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
