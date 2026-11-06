"""GPU checks for the dewy-morning heiligenschein on grass and leaves.

The fixture calls the real `shadeSurface` with the camera placed exactly along
the solar beam, so the retroreflective lobe is at its maximum. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
BLOCK_NEW = '''    if (foliage > 0.5) {
        float clock = float(worldTime % 24000);
        float dew = 1.0 - smoothstep(2000.0, 4600.0, clock);
        // A narrow backscatter lobe, about ten degrees wide at half height.
        // Six squarings keep it to multiplies on the low-end paths.
        float s = sat(dot(v, light));
        float s2 = s * s;
        float s4 = s2 * s2;
        float s8 = s4 * s4;
        float s16 = s8 * s8;
        float retro = s16 * s16 * s16; // s^48
        direct += m.albedo * sunRadiance * retro * dew * shadow *
                  (0.35 + 0.65 * nl) * 0.45 *
                  (1.0 - 0.70 * weatherRainAmount());
    }
'''
BLOCK_OLD = ''
SURFACE = '''
uniform vec3 testPlayer;
uniform float testId;
void main() {
    Material m=defaultMaterial(vec3(0.18,0.32,0.14),vec3(0.0,1.0,0.0));
    vec3 c=shadeSurface(m,testPlayer,vec2(0.0,1.0),testId);
    gl_FragColor=vec4(c,1.0);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/lighting.glsl')
    assert core.count(BLOCK_NEW) == 1
    if old:
        core = core.replace(BLOCK_NEW, BLOCK_OLD)
    head = '#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'
    return (head + core + SURFACE).replace(
        '#define CLOUD_QUALITY 3', '#define CLOUD_QUALITY 0')


class Heiligenschein(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, world_time=1000, height=0.30, rain=0.0,
               block_id=10001.0):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        for name in ('gbufferModelView', 'gbufferModelViewInverse',
                     'shadowModelView'):
            renderer.uniform(program, name, np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'shadowProjection',
                         np.diag([0.05, 0.05, 0.05, 1.0]).astype(np.float32))
        renderer.uniform(program, 'shadowtex0', 0)
        renderer.uniform(program, 'eyeBrightnessSmooth', [0, 240])
        renderer.uniform(program, 'worldTime', world_time)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', rain)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'testId', block_id)
        # v = light, the exact antisolar look direction of the observer.
        direction = np.array([0.0, height, -float(np.sqrt(1.0 - height ** 2))])
        renderer.uniform(program, 'sunPosition', list(direction * 300.0))
        renderer.uniform(program, 'shadowLightPosition', list(direction * 300.0))
        renderer.uniform(program, 'moonPosition', list(-direction * 300.0))
        renderer.uniform(program, 'testPlayer', list(-direction * 10.0))
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, renderer.white)
        renderer.full_screen()
        renderer.check('heiligenschein')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_dewy_grass_glows_toward_the_antisolar_point(self):
        new = self.sample(self.new)[0, 0]
        old = self.sample(self.old)[0, 0]
        self.assertGreater(float(new[1]), float(old[1]) * 1.10)

    def test_albedo_colour_is_preserved(self):
        new = self.sample(self.new)[0, 0]
        old = self.sample(self.old)[0, 0]
        added = np.maximum(new - old, 0.0)
        self.assertGreater(float(added[1]), float(added[0]))
        self.assertGreater(float(added[1]), float(added[2]))

    def test_noon_has_no_dew(self):
        new = self.sample(self.new, world_time=6000)
        old = self.sample(self.old, world_time=6000)
        np.testing.assert_array_equal(new, old)

    def test_night_has_no_dew(self):
        new = self.sample(self.new, world_time=18000)
        old = self.sample(self.old, world_time=18000)
        np.testing.assert_array_equal(new, old)

    def test_non_foliage_blocks_are_unchanged(self):
        new = self.sample(self.new, block_id=0.0)
        old = self.sample(self.old, block_id=0.0)
        np.testing.assert_array_equal(new, old)

    def test_rain_dims_the_glow(self):
        clear = float(self.sample(self.new)[0, 0, 1] -
                      self.sample(self.old)[0, 0, 1])
        rain = float(self.sample(self.new, rain=1.0)[0, 0, 1] -
                     self.sample(self.old, rain=1.0)[0, 0, 1])
        self.assertGreater(clear, 0.0)
        self.assertLess(rain, clear * 0.5)

    def test_deterministic(self):
        a = self.sample(self.new)
        b = self.sample(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
