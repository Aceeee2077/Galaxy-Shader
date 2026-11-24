"""Compile and budget checks for the low particle layer.

PARTICLE_LAYER 1 now evaluates one broad particle-noise field instead of two.
The fixture compiles the real function and checks the source budget and a
finite render.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
void main() {
    vec3 c = particleLayer(vec3(12.0, 72.0, 18.0), 26.0);
    gl_FragColor = vec4(c, 1.0);
}'''


def shader_source(quality=1):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/particles.glsl')
    core = core.replace('#define PARTICLE_LAYER 1',
                        f'#define PARTICLE_LAYER {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class ParticleLow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.program = cls.renderer.gl.compile(VERTEX, shader_source(1))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    def test_low_profile_drops_the_second_octave(self):
        source = shader_source(1)
        low = source[source.index('#if PARTICLE_LAYER == 1'):source.index('#else', source.index('#if PARTICLE_LAYER == 1'))]
        self.assertIn('particleNoise3(p)', low)
        self.assertNotIn('p * 2.7', low)
        high = shader_source(2)
        self.assertIn('p * 2.7', high)

    def test_low_layer_renders_finite(self):
        renderer = self.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], self.program)
        for name, value in [('frameTimeCounter', 30.0), ('rainStrength', 0.0),
                            ('thunderStrength', 0.0), ('wetness', 0.0),
                            ('worldTime', 6000), ('biome', 1),
                            ('biome_category', 1), ('biome_precipitation', 0),
                            ('temperature', 0.7), ('rainfall', 0.4)]:
            renderer.uniform(self.program, name, value)
        renderer.full_screen()
        renderer.check('particle low')
        data = renderer.read(W, H)[:, :, :3]
        self.assertTrue(np.isfinite(data).all())
        self.assertGreaterEqual(float(data.min()), 0.0)

    def test_deterministic(self):
        self.assertEqual(shader_source(1), shader_source(1))


if __name__ == '__main__':
    unittest.main()
