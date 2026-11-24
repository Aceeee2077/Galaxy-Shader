"""GPU checks for the top-profile atmosphere multiple scattering.

The extra sky term is only enabled at COSMIC_SKY_QUALITY 3, grows toward the
horizon and is exactly zero at the zenith and on lower profiles.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 8, 8
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DOMAIN = '''
uniform float testH;
void main() {
    vec3 s = atmosphereMultiScatter(vec3(1.0, 0.5, 0.2), testH);
    gl_FragColor = vec4(s, 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    core = core.replace('#define COSMIC_SKY_QUALITY 2',
                        f'#define COSMIC_SKY_QUALITY {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class AtmosphereMulti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.top = cls.renderer.gl.compile(VERTEX, shader_source(3))
        cls.low = cls.renderer.gl.compile(VERTEX, shader_source(2))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.top, cls.low):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program, h):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'testH', float(h))
        renderer.full_screen()
        renderer.check('atmosphere multi')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data.mean(axis=(0, 1))

    def test_top_profile_adds_light_near_the_horizon(self):
        horizon = self.sample(self.top, 0.0)
        zenith = self.sample(self.top, 1.0)
        self.assertGreater(float(horizon[0]), 0.09)
        self.assertLess(float(horizon[0]), 0.11)
        self.assertEqual(float(zenith[0]), 0.0)

    def test_lower_profiles_are_unchanged(self):
        self.assertEqual(float(self.sample(self.low, 0.0).sum()), 0.0)

    def test_atmosphere_uses_the_term(self):
        source = (SHADERS / 'lib/atmosphere.glsl').read_text(encoding='utf-8')
        self.assertIn('scatter+=atmosphereMultiScatter(scatter,h);', source)
        self.assertIn('COSMIC_SKY_QUALITY >= 3', source)


if __name__ == '__main__':
    unittest.main()
