"""GPU checks for the medium cloud self-shadow budget.

CLOUD_QUALITY 2 uses one longer light sample instead of two short ones. The
probe counts cloudDensity3D calls and compares the resulting shadow to the old
two-sample build at several heights.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW_TAPS = '''#if CLOUD_QUALITY == 2
    // One longer light sample instead of two short ones. The integrated path
    // length is close to the old 35 + 63 block span, so the medium profile
    // keeps the broad self-shadow gradient with one density evaluation.
    int taps = 1;
    float stepSize = 72.0;
'''
OLD_TAPS = '''#if CLOUD_QUALITY == 2
    int taps = 2;
    float stepSize = 35.0;
'''
DOMAIN = '''
uniform float testHeight;
uniform float testDetail;
void main() {
    float s = cloudLightShadow(vec3(0.0, testHeight, 0.0), testDetail);
    gl_FragColor = vec4(vec3(s), densityCalls);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/clouds.glsl')
    core = core.replace('#define CLOUD_QUALITY 3', '#define CLOUD_QUALITY 2')
    core = core.replace(NEW_TAPS, OLD_TAPS) if old else core
    definition = 'float cloudDensity3D(vec3 p, bool lightSample, float detail) {'
    assert core.count(definition) == 1
    core = core.replace(definition, 'float cloudDensity3DCore(vec3 p, bool lightSample, float detail) {')
    marker = '// Cheap forward light march'
    assert core.count(marker) == 1
    wrapper = '''float cloudDensity3D(vec3 p, bool lightSample, float detail) {
    densityCalls += 1.0;
    return cloudDensity3DCore(p, lightSample, detail);
}

'''
    core = core.replace(marker, wrapper + marker)
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float densityCalls=0.0;\n')
    return head + core + DOMAIN


class CloudLowShadow(unittest.TestCase):
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
    def sample(cls, program, height=220.0, detail=1.0):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testHeight', height)
        renderer.uniform(program, 'testDetail', detail)
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.uniform(program, 'currentDate', [1, 6, 1])
        renderer.uniform(program, 'sunPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'shadowLightPosition', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'moonPosition', [0.0, -1.0, 0.0])
        renderer.full_screen()
        renderer.check('cloud low shadow')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_medium_profile_uses_one_light_sample(self):
        new = self.sample(self.new, 220.0)
        old = self.sample(self.old, 220.0)
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))
        self.assertEqual(float(old[:, :, 3].sum()), float(2 * W * H))

    def test_shadow_stays_bounded_and_close(self):
        for height in (210.0, 230.0, 260.0, 300.0):
            new = self.sample(self.new, height)
            old = self.sample(self.old, height)
            self.assertGreaterEqual(float(new[:, :, 0].min()), 0.0)
            self.assertLessEqual(float(new[:, :, 0].max()), 1.0)
            self.assertLess(float(np.abs(new[:, :, 0] - old[:, :, 0]).max()), 0.35,
                            f'height {height}')

    def test_deterministic(self):
        np.testing.assert_array_equal(self.sample(self.new), self.sample(self.new))


if __name__ == '__main__':
    unittest.main()
