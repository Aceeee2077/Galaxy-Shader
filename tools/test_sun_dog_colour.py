"""GPU checks for the spectral tint on solar parhelia (sun dogs).

The fixture zooms on the right-hand sun dog of a 7-degree sun. It is an
engineering check, not a Minecraft screenshot or a scattering simulation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW = '''float dogSpectral = smoothstep(-0.012, 0.012,
                                       abs(azimuthFromSun) - 22.0 * deg);
        vec3 dogTint = mix(vec3(1.00, 0.56, 0.34), vec3(0.86, 0.90, 1.0),
                           dogSpectral);
        result += dogTint * dog * lowSun * 0.11;'''
OLD = '''result += mix(vec3(0.98, 0.72, 0.55), vec3(0.90, 0.92, 1.0), 0.35) *
                  dog * lowSun * 0.11;'''


def halo_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testLunar;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(15.0 + 15.0 * uv.x);
    float el = radians(14.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(iceHalo(ray, normalize(testSun), 1.0, vec3(1.0),
                                testLunar), 1.0);
}''')


class SunDogColourRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        source = halo_source()
        assert NEW in source
        cls.new = cls.renderer.gl.compile(VERTEX, source)
        cls.old = cls.renderer.gl.compile(VERTEX, source.replace(NEW, OLD))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, lunar=0.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(7.0)), np.sin(np.deg2rad(7.0)), 0.0])
        cls.renderer.uniform(program, 'testLunar', lunar)
        cls.renderer.full_screen()
        cls.renderer.check('sun dog colour')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def grid():
        u = (np.arange(W) + 0.5) / W
        v = (np.arange(H) + 0.5) / H
        az = np.broadcast_to(15.0 + 15.0 * u, (H, W))
        el = np.broadcast_to(14.0 * v[:, None], (H, W))
        return az, el

    def flanks(self):
        az, el = self.grid()
        near = np.abs(el - 7.0) < 1.6
        inner = near & (az > 20.3) & (az < 21.3)
        outer = near & (az > 22.7) & (az < 23.7)
        return inner, outer

    def test_sunward_flank_is_warm(self):
        image = self.image(self.new)
        inner, outer = self.flanks()
        warm_in = (image[inner, 0].mean()) / max(image[inner, 2].mean(), 1e-6)
        warm_out = (image[outer, 0].mean()) / max(image[outer, 2].mean(), 1e-6)
        self.assertGreater(warm_in, warm_out * 1.5)

    def test_outer_flank_is_cool(self):
        image = self.image(self.new)
        inner, outer = self.flanks()
        cool_out = image[outer, 2].mean() / max(image[outer, 0].mean(), 1e-6)
        cool_in = image[inner, 2].mean() / max(image[inner, 0].mean(), 1e-6)
        self.assertGreater(cool_out, cool_in * 1.5)

    def test_previous_tint_matches_away_from_the_dog(self):
        new = self.image(self.new)
        old = self.image(self.old)
        az, el = self.grid()
        far = (az > 27.0) & (el < 4.0)
        self.assertTrue(far.any())
        np.testing.assert_allclose(new[far], old[far], atol=2e-4)

    def test_lunar_dogs_are_unchanged(self):
        new = self.image(self.new, lunar=1.0)
        old = self.image(self.old, lunar=1.0)
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_deterministic(self):
        a = self.image(self.new)
        b = self.image(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
