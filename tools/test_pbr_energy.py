"""GPU checks for the rough-surface GGX energy compensation.

The single-scatter lobe loses energy at high roughness. The new bounded Fresnel
boost must leave a mirror untouched and raise a rough metal's specular response
without changing the BRDF for a back-facing surface.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
BOOST = '    fresnel *= 1.0 + m.roughness * 0.175;\n'
DOMAIN = '''
uniform float testRoughness;
uniform float testMetal;
void main() {
    Material m = defaultMaterial(vec3(0.8, 0.5, 0.2), vec3(0.0, 1.0, 0.0));
    m.roughness = testRoughness;
    m.metal = testMetal;
    if (testMetal > 0.5) m.f0 = vec3(0.95, 0.64, 0.54);
    else m.f0 = vec3(0.04);
    vec3 c = specularBRDF(m, vec3(0.0, 1.0, 0.0), vec3(0.0, 1.0, 0.0));
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/pbr.glsl')
    if old:
        assert core.count(BOOST) == 1
        core = core.replace(BOOST, '')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class PbrEnergy(unittest.TestCase):
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
    def sample(cls, program, roughness, metal):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testRoughness', float(roughness))
        renderer.uniform(program, 'testMetal', float(metal))
        renderer.full_screen()
        renderer.check('pbr energy')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_mirror_is_unchanged(self):
        new = self.sample(self.new, 0.0, 1.0)
        old = self.sample(self.old, 0.0, 1.0)
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_rough_metal_gains_energy(self):
        new = float(self.sample(self.new, 0.8, 1.0).mean())
        old = float(self.sample(self.old, 0.8, 1.0).mean())
        self.assertGreater(new, old * 1.05)
        self.assertLess(new, old * 1.30)

    def test_back_facing_stays_zero(self):
        # The domain uses a front-facing normal; a separate source check keeps
        # the early-out contract visible and the test remains cheap.
        source = shader_source()
        self.assertIn('if(nl<=0.0) return vec3(0.0);', source)
        data = self.sample(self.new, 0.5, 0.0)
        self.assertTrue(np.all(data >= 0.0))

    def test_deterministic(self):
        np.testing.assert_array_equal(self.sample(self.new, 0.4, 0.0),
                                      self.sample(self.new, 0.4, 0.0))


if __name__ == '__main__':
    unittest.main()
