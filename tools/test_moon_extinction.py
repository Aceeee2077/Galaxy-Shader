"""GPU checks for the low-moon reddening.

The fixture calls `moonSky` directly around the moon direction. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 180
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
TINT_NEW = 'vec3(1.00, 0.60, 0.36), vec3(1.0)'
TINT_OLD = 'vec3(1.0), vec3(1.0)'


def shader_source(old=False):
    core = (expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/atmospheric_refraction.glsl') +
            expand(SHADERS / 'lib/moon.glsl'))
    assert TINT_NEW in core
    if old:
        core = core.replace(TINT_NEW, TINT_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
uniform float testElevation;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 moon = normalize(vec3(cos(radians(testElevation)),
                               sin(radians(testElevation)), 0.0));
    vec3 helper = abs(moon.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(moon, helper));
    vec3 up = cross(right, moon);
    float az = radians((uv.x - 0.5) * 60.0);
    float el = radians((uv.y - 0.5) * 60.0);
    vec3 ray = normalize(moon + right * tan(az) + up * tan(el));
    gl_FragColor = vec4(moonSky(ray, 1.0, 0.0), 1.0);
}''')


class LowMoonReddening(unittest.TestCase):
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
    def image(cls, program, elevation):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testElevation', float(elevation))
        cls.renderer.uniform(program, 'sunPosition', [300.0, 0.0, 0.0])
        cls.renderer.uniform(program, 'moonPosition',
                             [float(np.cos(np.deg2rad(elevation))) * 300.0,
                              float(np.sin(np.deg2rad(elevation))) * 300.0, 0.0])
        cls.renderer.uniform(program, 'moonPhase', 0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('moon extinction')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_high_moon_is_unchanged(self):
        new = self.image(self.new, 45.0)
        old = self.image(self.old, 45.0)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_low_moon_is_warmer(self):
        new = self.image(self.new, 3.0)[:, :, :3]
        old = self.image(self.old, 3.0)[:, :, :3]
        self.assertGreater(float(new[:, :, 0].mean() / max(new[:, :, 2].mean(), 1e-6)),
                           float(old[:, :, 0].mean() / max(old[:, :, 2].mean(), 1e-6)))

    def test_low_moon_loses_blue_light(self):
        new = self.image(self.new, 3.0)[:, :, :3]
        old = self.image(self.old, 3.0)[:, :, :3]
        self.assertLess(float(new[:, :, 2].mean()), float(old[:, :, 2].mean()))

    def test_low_moon_stays_visible(self):
        new = self.image(self.new, 3.0)[:, :, :3]
        self.assertGreater(float(new.max()), 0.05)

    def test_mid_moon_is_between_the_two(self):
        high = float(self.image(self.new, 45.0)[:, :, :3][:, :, 2].mean())
        mid = float(self.image(self.new, 12.0)[:, :, :3][:, :, 2].mean())
        low = float(self.image(self.new, 3.0)[:, :, :3][:, :, 2].mean())
        self.assertLess(low, mid)
        self.assertLess(mid, high)

    def test_deterministic(self):
        a = self.image(self.new, 12.0)
        b = self.image(self.new, 12.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
