"""GPU checks for sharing one directional radiance across a terrain fragment.

The probe counts calls to `directionalRadiance` per pixel while rendering the
real `shadeSurface`. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DECL_NEW = '    vec3 sunRadiance=directionalRadiance();\n'
DECL_OLD = ''
DIRECT_NEW = ('    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*'
              'sunRadiance*shadow;')
DIRECT_OLD = ('    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*'
              'directionalRadiance()*shadow;')
LEAF_NEW = '(0.06+0.36*forward)*(1.0-nl)*sunRadiance*shadow;'
LEAF_OLD = '(0.06+0.36*forward)*(1.0-nl)*directionalRadiance()*shadow;'
BOUNCE_NEW = 'direct+=m.albedo*(1.0-m.metal)*sunRadiance*0.035*'
BOUNCE_OLD = 'direct+=m.albedo*(1.0-m.metal)*directionalRadiance()*0.035*'
DEFINITION = 'vec3 directionalRadiance() {'
RENAMED = 'vec3 radianceCore() {'
WRAPPER = '''
vec3 directionalRadiance(){
    radianceCalls+=1.0;
    return radianceCore();
}
'''
SURFACE = '''
uniform float testSky;
void main() {
    Material m=defaultMaterial(vec3(0.18),vec3(0.0,1.0,0.0));
    vec3 c=shadeSurface(m,vec3(0.0,0.0,-10.0),vec2(0.0,testSky),0.0);
    gl_FragColor=vec4(c,radianceCalls);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/lighting.glsl')
    for snippet in (DECL_NEW, DIRECT_NEW, LEAF_NEW, BOUNCE_NEW):
        assert core.count(snippet) == 1, snippet
    assert core.count(DEFINITION) == 1
    if old:
        core = core.replace(DECL_NEW, DECL_OLD)
        core = core.replace(DIRECT_NEW, DIRECT_OLD)
        core = core.replace(LEAF_NEW, LEAF_OLD)
        core = core.replace(BOUNCE_NEW, BOUNCE_OLD)
    core = core.replace(DEFINITION, RENAMED)
    head = ('#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'
            'float radianceCalls=0.0;\nvec3 directionalRadiance();\n')
    return (head + core + WRAPPER + SURFACE).replace(
        '#define CLOUD_QUALITY 3', '#define CLOUD_QUALITY 0')


class RadianceCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))
        cls.dark = cls.renderer.texture(1, 1, data=np.zeros((1, 1, 4), np.float32))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, sky=1.0, height=0.4):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        for name in ('gbufferModelView', 'gbufferModelViewInverse',
                     'shadowModelView'):
            renderer.uniform(program, name, np.eye(4, dtype=np.float32))
        projection = np.diag([0.05, 0.05, 0.05, 1.0]).astype(np.float32)
        renderer.uniform(program, 'shadowProjection', projection)
        renderer.uniform(program, 'shadowtex0', 0)
        renderer.uniform(program, 'eyeBrightnessSmooth', [0, 240])
        renderer.uniform(program, 'testSky', sky)
        direction = [0.0, height, -float(np.sqrt(1.0 - height * height))]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, cls.dark)
        renderer.full_screen()
        renderer.check('radiance cache')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_each_fragment_evaluates_radiance_once(self):
        new = self.sample(self.new)
        old = self.sample(self.old)
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))
        self.assertEqual(float(old[:, :, 3].sum()), float(3 * W * H))

    def test_shading_is_unchanged(self):
        new = self.sample(self.new)[:, :, :3]
        old = self.sample(self.old)[:, :, :3]
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_shaded_terrain_is_unchanged(self):
        new = self.sample(self.new, sky=0.0)[:, :, :3]
        old = self.sample(self.old, sky=0.0)[:, :, :3]
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_water_shares_the_radiance(self):
        source = (SHADERS / 'program' / 'translucent.fsh').read_text(encoding='utf-8')
        self.assertEqual(source.count('directionalRadiance()'), 1)
        self.assertIn('specularBRDF(m,safeNormalize(-vPlayer),lightDirection())*sunRadiance*',
                      source)
        self.assertIn('foamLight+=sunRadiance*', source)

    def test_deterministic(self):
        a = self.sample(self.new)
        b = self.sample(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
