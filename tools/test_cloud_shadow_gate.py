"""GPU check for the zero-strength cloud-shadow gate.

With CLOUD_SHADOW_STRENGTH=0 the cloud density is multiplied by zero before it
can change the result. The probe counts cloudDensity calls and verifies the new
early return is pixel-identical to the previous evaluation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE = ('    // A zero strength makes the density term exactly zero. Skip the noise\n'
        '    // lookup entirely instead of evaluating it and multiplying by zero.\n'
        '    if (CLOUD_SHADOW_STRENGTH <= 0.0) return 1.0;\n')
DOMAIN = '''
uniform vec3 testWorld;
void main() {
    float v = cloudShadow(testWorld);
    gl_FragColor = vec4(vec3(v), densityCalls);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/cloud_field.glsl')
    core = core.replace('#define CLOUD_SHADOW_STRENGTH 0.8',
                        '#define CLOUD_SHADOW_STRENGTH 0.0')
    if old:
        assert core.count(GATE) == 1
        core = core.replace(GATE, '')
    definition = 'float cloudDensity(vec2 position) {'
    assert core.count(definition) == 1
    core = core.replace(definition, 'float cloudDensityCore(vec2 position) {')
    marker = 'float cloudShadow(vec3 world) {'
    assert core.count(marker) == 1
    wrapper = ('float cloudDensity(vec2 position) {\n'
               '    densityCalls += 1.0;\n'
               '    return cloudDensityCore(position);\n'
               '}\n\n')
    core = core.replace(marker, wrapper + marker)
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float densityCalls=0.0;\nfloat cloudDensity(vec2 position);\n')
    return head + core + DOMAIN


class CloudShadowGate(unittest.TestCase):
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
    def sample(cls, program):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testWorld', [0.0, 70.0, 0.0])
        renderer.uniform(program, 'shadowLightPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'sunPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'moonPosition', [0.0, -1.0, 0.0])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.uniform(program, 'currentDate', [1, 6, 1])
        renderer.full_screen()
        renderer.check('cloud shadow gate')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_zero_strength_skips_density(self):
        new = self.sample(self.new)
        old = self.sample(self.old)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_output_is_unchanged(self):
        new = self.sample(self.new)[:, :, :3]
        old = self.sample(self.old)[:, :, :3]
        np.testing.assert_array_equal(new, old)

    def test_deterministic(self):
        np.testing.assert_array_equal(self.sample(self.new), self.sample(self.new))


if __name__ == '__main__':
    unittest.main()
