"""GPU checks for the rotating Milky Way sheet.

The fixture samples galaxyNebula() directly over an equirectangular upper
hemisphere, so the assertions describe the authored sky function rather than a
post-processed gameplay frame. Rays are synthetic; this is not a game capture.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 128, 64
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


class NightGalaxyRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/night_sky.glsl') +
                    '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.5707963 + 0.005;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(galaxyNebula(ray), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def sky(cls, theta):
        """theta in units of pi: 1.10 is dusk, 1.50 midnight, 1.90 dawn."""
        sun = np.array([np.cos(theta * np.pi), np.sin(theta * np.pi), 0.0],
                       dtype=np.float32)
        cls.renderer.uniform(cls.program, 'sunPosition', sun * 100.0)
        cls.renderer.uniform(cls.program, 'moonPosition', -sun * 100.0)
        cls.renderer.uniform(cls.program, 'shadowLightPosition',
                             (-sun if sun[1] < 0 else sun) * 100.0)
        cls.renderer.full_screen()
        cls.renderer.check('night galaxy')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def brightness(self, image):
        return image @ np.array([0.2126, 0.7152, 0.0722], np.float32)

    def test_deterministic(self):
        a = self.sky(1.50)
        b = self.sky(1.50)
        np.testing.assert_array_equal(a, b, 'Galaxy must be stable between frames')

    def test_twilight_and_horizon_gate(self):
        day = self.sky(0.50)          # sun above the horizon
        twilight = self.sky(1.02)     # sun just below the horizon
        self.assertLess(float(day.max()), 1e-5, 'No galaxy in daylight')
        self.assertLess(float(twilight.max()), 0.05,
                        'Galaxy waits for astronomical twilight')

    def test_band_rises_overhead_and_sets(self):
        dusk = self.brightness(self.sky(1.10))
        midnight = self.brightness(self.sky(1.50))
        dawn = self.brightness(self.sky(1.90))
        rows = np.arange(H, dtype=np.float32)[:, None] + 0.5
        elevation = lambda im: float((im * rows).sum() / max(im.sum(), 1e-8))
        self.assertGreater(elevation(midnight), elevation(dusk) + 8.0,
                           'The band climbs from its first side')
        self.assertGreater(elevation(midnight), elevation(dawn) + 8.0,
                           'The band descends toward the other side')

    def test_one_continuous_sheet_at_midnight(self):
        midnight = self.brightness(self.sky(1.50))
        dusk = self.brightness(self.sky(1.10))
        peak = max(float(midnight.max()), 1e-8)
        columns = midnight.max(axis=0) > peak * 0.02
        # Azimuth bins are narrower than the band, so a continuous sheet over
        # the whole dome must light almost all of them near the meridian.
        self.assertGreater(float(columns.mean()), 0.85,
                           'Midnight band spans the sky as one sheet')
        dusk_columns = dusk.max(axis=0) > peak * 0.02
        self.assertLess(float(dusk_columns.mean()), float(columns.mean()) - 0.1,
                        'At dusk the band is still an arc on one side')

    def test_grain_and_dust_structure(self):
        image = self.brightness(self.sky(1.50))
        detail = np.abs(image[:, 1:] - image[:, :-1]).mean()
        self.assertGreater(float(detail), 1e-4,
                           'Band must not be a featureless smooth blob')
        # A scan across the brightest part of the sheet must contain a dark
        # lane between brighter shoulders.
        y, x = np.unravel_index(int(image.argmax()), image.shape)
        lo, hi = max(0, y - 5), min(H, y + 6)
        profile = image[lo:hi, x]
        self.assertGreater(float(profile.max() - profile.min()), float(profile.max()) * 0.12,
                           'Dust lane must carve a visible trough')


if __name__ == '__main__':
    unittest.main()
