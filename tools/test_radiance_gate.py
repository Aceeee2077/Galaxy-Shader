"""GPU checks for skipping directional radiance when every direct lobe is zero.

`shadeSurface` has three direct lobes: diffuse/specular, thin-leaf transmission
and the warm shadow bounce. A back-facing, fully lit, non-foliage fragment
makes all three exactly zero, so evaluating the atmospheric transmittance chain
there is pure waste. The probe counts calls to the real `directionalRadiance`
and compares the complete shading against the previous build.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DEFINITION = 'vec3 directionalRadiance() {'
RENAMED = 'vec3 radianceCore() {'
WRAPPER = '''
vec3 directionalRadiance(){
    radianceCalls+=1.0;
    return radianceCore();
}
'''
SURFACE = '''
uniform vec3 testNormal;
uniform float testSky;
uniform float testId;
void main() {
    Material m=defaultMaterial(vec3(0.18),safeNormalize(testNormal));
    vec3 c=shadeSurface(m,vec3(0.0,0.0,-10.0),vec2(0.0,testSky),testId);
    gl_FragColor=vec4(c,radianceCalls);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/lighting.glsl')
    assert core.count(DEFINITION) == 1
    # The old build evaluates radiance unconditionally. Reconstruct that single
    # line so both programs share every other part of the real shader.
    if old:
        core = core.replace(
            '    bool needsRadiance = nl > 0.0 || foliage > 0.5 || shadow < 1.0;\n'
            '    vec3 sunRadiance = needsRadiance ? directionalRadiance() : vec3(0.0);',
            '    vec3 sunRadiance = directionalRadiance();')
    core = core.replace(DEFINITION, RENAMED)
    head = ('#version 330 compatibility\n#define DIMENSION 0\n'
            'uniform float testCloud;\n'
            'float radianceCalls=0.0;\nvec3 directionalRadiance();\n')
    core = core.replace('vCloudShadow', 'testCloud')
    return (head + core + WRAPPER + SURFACE).replace(
        '#define CLOUD_QUALITY 3', '#define CLOUD_QUALITY 0')


class RadianceGate(unittest.TestCase):
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
    def sample(cls, program, normal=(0.0, 1.0, 0.0), sky=0.0, ident=0.0,
               light=(0.0, 0.0, -1.0), texture=None, cloud=1.0):
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
        renderer.uniform(program, 'testNormal', list(normal))
        renderer.uniform(program, 'testSky', sky)
        renderer.uniform(program, 'testId', ident)
        renderer.uniform(program, 'testCloud', cloud)
        renderer.uniform(program, 'sunPosition', list(light))
        renderer.uniform(program, 'shadowLightPosition', list(light))
        renderer.uniform(program, 'moonPosition', [-v for v in light])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1,
                      texture if texture is not None else cls.dark)
        renderer.full_screen()
        renderer.check('radiance gate')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_back_facing_lit_terrain_skips_radiance(self):
        new = self.sample(self.new, sky=0.5)
        old = self.sample(self.old, sky=0.5)
        self.assertEqual(float(new[:, :, 3].sum()), 0.0)
        self.assertEqual(float(old[:, :, 3].sum()), float(W * H))

    def test_back_facing_terrain_still_shades_identically(self):
        new = self.sample(self.new, sky=0.5)[:, :, :3]
        old = self.sample(self.old, sky=0.5)[:, :, :3]
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_foliage_keeps_the_transmission_lobe(self):
        new = self.sample(self.new, ident=10001.0)
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_cloud_shaded_back_face_keeps_the_bounce_lobe(self):
        new = self.sample(self.new, sky=0.5, cloud=0.6)
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_front_facing_terrain_keeps_the_direct_lobe(self):
        new = self.sample(self.new, normal=(0.0, 1.0, 0.0), light=(0.0, 1.0, 0.0))
        self.assertEqual(float(new[:, :, 3].sum()), float(W * H))

    def test_deterministic(self):
        a = self.sample(self.new)
        b = self.sample(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
