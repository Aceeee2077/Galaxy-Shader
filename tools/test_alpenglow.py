"""GPU checks for the alpenglow term on the cloud deck.

The fixture calls `volumetricClouds` directly with a fixed sky. It is an
engineering check, not a Minecraft screenshot. The sun elevation is set through
`sunPosition`, so the same harness reaches noon, deep night and twilight.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '''    float alpenglowGate = smoothstep(-0.30, -0.13, sun.y) *
                          (1.0 - smoothstep(-0.02, 0.07, sun.y));'''
GATE_OLD = '    float alpenglowGate = -1.0;'


def shader_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/clouds.glsl') +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 40.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = volumetricClouds(vec3(0.10, 0.16, 0.26), ray,
                                   vec3(0.0, 70.0, 0.0), false);
    gl_FragColor = vec4(colour, 1.0);
}''')


class AlpenglowTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = shader_source()
        assert GATE_NEW in base
        cls.new = cls.renderer.gl.compile(VERTEX, base)
        cls.old = cls.renderer.gl.compile(VERTEX, base.replace(GATE_NEW, GATE_OLD))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_height):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.arcsin(np.clip(sun_height, -1.0, 1.0))
        direction = [float(np.cos(elevation)), float(sun_height), 0.0]
        cls.renderer.uniform(program, 'sunPosition',
                             [component * 300.0 for component in direction])
        cls.renderer.uniform(program, 'shadowLightPosition',
                             [component * 300.0 for component in direction])
        cls.renderer.uniform(program, 'moonPosition',
                             [-component * 300.0 for component in direction])
        cls.renderer.uniform(program, 'worldTime', 6000)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', 0.0)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', 0.0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('alpenglow')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_daytime_clouds_are_unchanged(self):
        new = self.image(self.new, 0.60)
        old = self.image(self.old, 0.60)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_deep_night_clouds_are_unchanged(self):
        new = self.image(self.new, -0.60)
        old = self.image(self.old, -0.60)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_twilight_clouds_brighten(self):
        new = self.image(self.new, -0.18)[:, :, :3]
        old = self.image(self.old, -0.18)[:, :, :3]
        self.assertGreater(float(new.mean()), float(old.mean()))

    def test_twilight_added_light_is_red_biased(self):
        delta = self.image(self.new, -0.18)[:, :, :3] - \
                self.image(self.old, -0.18)[:, :, :3]
        self.assertGreater(float(delta[:, :, 0].mean()), 0.0)
        self.assertGreater(float(delta[:, :, 0].mean()),
                           float(delta[:, :, 2].mean()))

    def test_twilight_glow_leans_toward_the_sun(self):
        delta = self.image(self.new, -0.18)[:, :, :3] - \
                self.image(self.old, -0.18)[:, :, :3]
        towards = float(delta[:, :W // 8].mean())
        away = float(delta[:, W * 3 // 8:W * 5 // 8].mean())
        self.assertGreater(towards, away)

    def test_deterministic(self):
        a = self.image(self.new, -0.18)
        b = self.image(self.new, -0.18)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
