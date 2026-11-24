"""GPU checks for the top-profile rain gust shear.

WEATHER_QUALITY 4 adds a slow gust to the streak field; lower profiles return
exactly zero and keep their old rain silhouette.
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
    float s = rainWindShear(vec2(12.0, 18.0), vec2(0.84, 0.38), 30.0, 0.25);
    gl_FragColor = vec4(vec3(s), 1.0);
}'''


def shader_source(quality):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/weather.glsl')
    core = core.replace('#define WEATHER_QUALITY 3',
                        f'#define WEATHER_QUALITY {quality}')
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + DOMAIN


class RainShear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.top = cls.renderer.gl.compile(VERTEX, shader_source(4))
        cls.low = cls.renderer.gl.compile(VERTEX, shader_source(2))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.top, cls.low):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sample(cls, program):
        renderer = cls.renderer
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.full_screen()
        renderer.check('rain shear')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return float(data.mean())

    def test_top_profile_has_a_gust(self):
        self.assertNotEqual(self.sample(self.top), 0.0)

    def test_low_profile_is_exactly_zero(self):
        self.assertEqual(self.sample(self.low), 0.0)

    def test_weather_program_uses_the_helper(self):
        source = (SHADERS / 'program' / 'weather.fsh').read_text(encoding='utf-8')
        self.assertIn('rainWindShear(vPlayer.xz + cameraPosition.xz, wind', source)
        self.assertIn('#if WEATHER_QUALITY >= 4', source)


if __name__ == '__main__':
    unittest.main()
