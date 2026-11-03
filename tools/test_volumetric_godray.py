"""GPU checks for the zero-strength god-ray early-out.

The volumetric light integral costs 8-40 shadow taps per pixel. When
GODRAY_STRENGTH is zero the shaft term is identically zero, so the shader now
skips the loop and keeps only the independent lightning flash. These tests
compare against the previous code at strength 0 and 1, and verify that a storm
flash survives at zero strength while the clear-sky result is exactly zero.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 96
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def light_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/atmosphere.glsl') +
            expand(SHADERS / 'lib/cloud_field.glsl') +
            expand(SHADERS / 'lib/volumetrics.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testPlayer;
void main() {
    gl_FragColor = vec4(volumetricLight(testPlayer, false), 1.0);
}''')


def with_strength(source, value):
    return source.replace('#define GODRAY_STRENGTH 1.0',
                          f'#define GODRAY_STRENGTH {value}')


def ungated(source):
    return source.replace('    if (GODRAY_STRENGTH > 0.0) {\n', '    {\n')


class VolumetricGodrayRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        base = light_source()
        cls.on1 = cls.renderer.gl.compile(VERTEX, with_strength(base, '1.0'))
        cls.on0 = cls.renderer.gl.compile(VERTEX, with_strength(base, '0.0'))
        cls.old1 = cls.renderer.gl.compile(
            VERTEX, ungated(with_strength(base, '1.0')))
        cls.old0 = cls.renderer.gl.compile(
            VERTEX, ungated(with_strength(base, '0.0')))
        ones = np.ones((4, 4, 4), np.float32)
        cls.shadow = cls.renderer.texture(4, 4, data=ones)

    @classmethod
    def tearDownClass(cls):
        for program in (cls.on1, cls.on0, cls.old1, cls.old0):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, player=(0.0, 4.0, 2.0), rain=0.0, thunder=0.0,
              flash=0.0, water=0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testPlayer', list(player))
        cls.renderer.uniform(program, 'shadowProjection',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'shadowModelView',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'shadowDistance', 100.0)
        cls.renderer.uniform(program, 'shadowMapResolution', 2048)
        cls.renderer.uniform(program, 'sunPosition', [0.0, 34.2, 94.0])
        cls.renderer.uniform(program, 'moonPosition', [0.0, -34.2, -94.0])
        cls.renderer.uniform(program, 'cameraPosition', [0.0, 70.0, 0.0])
        cls.renderer.uniform(program, 'rainStrength', rain)
        cls.renderer.uniform(program, 'thunderStrength', thunder)
        cls.renderer.uniform(program, 'lightningBoltPosition',
                             [0.0, 0.0, 0.0, flash])
        cls.renderer.uniform(program, 'eyeBrightnessSmooth', [220, 220])
        cls.renderer.uniform(program, 'isEyeInWater', int(water))
        cls.renderer.uniform(program, 'frameCounter', 0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.call('glActiveTexture', None, [U], 0x84C0)
        cls.renderer.call('glBindTexture', None, [U, U], 0x0DE1, cls.shadow)
        cls.renderer.uniform(program, 'shadowtex0', 0)
        cls.renderer.full_screen()
        cls.renderer.check('volumetric god rays')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        np.testing.assert_array_equal(self.image(self.on1),
                                      self.image(self.on1))

    def test_enabled_matches_previous_code(self):
        np.testing.assert_array_equal(
            self.image(self.on1), self.image(self.old1),
            'A non-zero slider must keep the previous shaft integral')

    def test_disabled_matches_previous_code(self):
        np.testing.assert_array_equal(
            self.image(self.on0, rain=0.7, thunder=0.8, flash=1.0),
            self.image(self.old0, rain=0.7, thunder=0.8, flash=1.0),
            'Zero strength must keep the previous output')

    def test_disabled_clear_sky_is_zero(self):
        data = self.image(self.on0)
        self.assertEqual(float(np.abs(data).max()), 0.0,
                         'Without shafts or lightning the result must be zero')

    def test_disabled_keeps_lightning(self):
        data = self.image(self.on0, rain=1.0, thunder=1.0, flash=1.0)
        self.assertGreater(float(data.max()), 0.0,
                           'A storm flash must survive a zero slider')
        ratio = data[..., 2].max() / max(data[..., 1].max(), 1e-9)
        self.assertAlmostEqual(ratio, 0.48 / 0.30, delta=1e-2,
                               msg='Only the blue lightning tint may remain')

    def test_disabled_underwater_is_zero(self):
        data = self.image(self.on0, player=(0.0, 1.0, 2.0), water=1)
        self.assertEqual(float(np.abs(data).max()), 0.0,
                         'Underwater has no lightning term to keep')
        self.assertGreater(float(self.image(self.on1, player=(0.0, 1.0, 2.0),
                                            water=1).max()), 0.0,
                           'Enabled underwater shafts must remain visible')


if __name__ == '__main__':
    unittest.main()
