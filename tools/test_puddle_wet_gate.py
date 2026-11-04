"""GPU checks for the puddle-noise gate on dried-out surfaces.

The fixture runs the authored puddle block from `geometry.fsh` over a grid of
wetness, exposure and facing values. It is an engineering check, not a
Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW = '''    if(wet>0.0) {
        float puddleNoise=valueNoise((vPlayer.xz+cameraPosition.xz)*0.35);
        float puddle=step(0.58,puddleNoise)*smoothstep(0.80,0.98,vLight.y)*upward*wet;
        m.roughness=mix(m.roughness,0.02,puddle);
        m.albedo*=1.0-0.12*puddle;
    }'''
OLD = NEW.replace('if(wet>0.0) {', 'if(wet>-1.0) {')
PUDDLE_NOISE = '        float puddleNoise=valueNoise('


def block(text):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float puddleCalls=0.0;\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/pbr.glsl') +
            '''
uniform vec2 testResolution;
uniform float testWet;
uniform float testUpward;
uniform float testLight;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 vPlayer = vec3(uv.x * 20.0, 0.0, uv.y * 20.0);
    vec2 vLight = vec2(0.0, testLight);
    float wet = testWet;
    float upward = testUpward;
    Material m;
    m.albedo = vec3(0.55, 0.62, 0.44);
    m.roughness = 0.55;
    float puddleNoise = 0.0;
    float puddle = 0.0;
''' + text + '''
    gl_FragColor = vec4(m.albedo, puddleCalls + m.roughness);
}''')


def instrument(text):
    return text.replace(PUDDLE_NOISE, '        puddleCalls+=1.0;\n' + PUDDLE_NOISE)


class PuddleWetGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        source = SHADERS / 'program' / 'geometry.fsh'
        authored = source.read_text(encoding='utf-8')
        assert NEW in authored
        cls.new = cls.renderer.gl.compile(VERTEX, instrument(block(NEW)))
        cls.old = cls.renderer.gl.compile(VERTEX, instrument(block(OLD)))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, wet, upward=1.0, light=1.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'cameraPosition', [3.0, 64.0, 7.0])
        cls.renderer.uniform(program, 'testWet', float(wet))
        cls.renderer.uniform(program, 'testUpward', float(upward))
        cls.renderer.uniform(program, 'testLight', float(light))
        cls.renderer.full_screen()
        cls.renderer.check('puddle wet gate')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_dry_surface_output_is_unchanged(self):
        new = self.image(self.new, 0.0)
        old = self.image(self.old, 0.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_dry_surface_skips_the_puddle_noise(self):
        new = float(self.image(self.new, 0.0)[:, :, 3].sum())
        old = float(self.image(self.old, 0.0)[:, :, 3].sum())
        self.assertLess(new, old)

    def test_wet_surface_still_runs_the_puddle(self):
        new = self.image(self.new, 0.8)
        old = self.image(self.old, 0.8)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)
        self.assertEqual(float(new[:, :, 3].sum()), float(old[:, :, 3].sum()))

    def test_downward_face_is_unchanged(self):
        new = self.image(self.new, 1.0, 0.0)
        old = self.image(self.old, 1.0, 0.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_deterministic(self):
        a = self.image(self.new, 0.8)
        b = self.image(self.new, 0.8)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
