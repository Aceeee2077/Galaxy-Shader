"""GPU checks for the twilight and airglow optics.

The fixture samples the authored sky functions directly over an equirectangular
upper hemisphere. Rays and sun positions are synthetic; this is not a game
capture. Assertions describe geometry, gating and colour, not final exposure.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 160, 96
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'

BELT, ZODIAC, AIRGLOW, SHADOW, COMBINED, OVERCAST = range(6)
ANTI = np.s_[:, :28]          # az near +/-180 degrees on both image edges
SUN_SIDE = np.s_[:, 70:90]    # az near 0 degrees, centred on the sun
LOW = np.s_[0:48, :]          # below ~17 degrees
HIGH = np.s_[56:, :]


class TwilightOpticsRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/twilight_optics.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform int testMode;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.70;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 sun = normalize(testSun);
    vec3 value;
    if (testMode == 0) value = beltOfVenus(ray, sun);
    else if (testMode == 1) value = zodiacalLight(ray, sun);
    else if (testMode == 2) value = airglow(ray, sun);
    else if (testMode == 3) value = vec3(earthShadowMask(ray, sun));
    else if (testMode == 4) value = twilightOptics(ray, sun, 0.0);
    else value = twilightOptics(ray, sun, 1.0);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testMode', BELT)
        cls.renderer.uniform(cls.program, 'testSun', [1.0, -0.06, 0.0])

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, mode, sun_height, time=40.0):
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        cls.renderer.uniform(cls.program, 'testSun',
                             [horizontal, sun_height, 0.0])
        cls.renderer.uniform(cls.program, 'testMode', mode)
        cls.renderer.uniform(cls.program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('twilight optics')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, region=None):
        values = image if region is None else image[region]
        return float(values.max())

    def test_deterministic(self):
        a = self.image(COMBINED, -0.08, time=123.0)
        b = self.image(COMBINED, -0.08, time=123.0)
        np.testing.assert_array_equal(a, b, 'Optics must be frame-stable')

    def test_daylight_gate(self):
        for mode in (BELT, ZODIAC, AIRGLOW):
            self.assertLess(self.peak(self.image(mode, 0.30)), 1e-6,
                            f'Effect {mode} must vanish in daylight')

    def test_belt_is_anti_solar_and_pink(self):
        image = self.image(BELT, -0.06)
        self.assertGreater(self.peak(image, ANTI), 0.008)
        self.assertLess(self.peak(image, SUN_SIDE), 1e-5)
        y, x = np.unravel_index(int(image[ANTI].argmax()),
                                image[ANTI].shape[:2])
        red, green, blue = (float(image[y, x, c]) for c in range(3))
        self.assertGreater(red, green * 1.3, 'Belt keeps a pink cast')
        self.assertGreater(red, blue * 1.2, 'Belt must not read blue')

    def test_shadow_wedge_sits_below_the_belt(self):
        shadow = self.image(SHADOW, -0.06)
        belt = self.image(BELT, -0.06)
        anti_shadow = shadow[ANTI]
        anti_belt = belt[ANTI]
        self.assertGreater(float(anti_shadow.max()), 0.25,
                           'Earth shadow must cast a visible wedge')
        self.assertLess(float(shadow[SUN_SIDE].max()), 1e-5)
        shadow_row = int(anti_shadow.mean(axis=1).argmax())
        belt_row = int(anti_belt.mean(axis=1).argmax())
        self.assertGreater(belt_row, shadow_row + 3,
                           'Belt of Venus caps the shadow instead of replacing it')

    def test_zodiacal_cone_faces_the_sun(self):
        image = self.image(ZODIAC, -0.10)
        sun_side = self.peak(image, SUN_SIDE)
        anti_side = self.peak(image, ANTI)
        self.assertGreater(sun_side, 0.004)
        self.assertGreater(sun_side, anti_side * 5.0,
                           'Zodiacal light rises on the sun side only')
        self.assertGreater(self.peak(image, LOW), self.peak(image, HIGH) * 2.0,
                           'Cone must fade with elevation')
        midnight = self.image(ZODIAC, -0.80)
        self.assertLess(self.peak(midnight), 1e-6,
                        'Zodiacal light is a twilight phenomenon')

    def test_airglow_night_only_and_green(self):
        midnight = self.image(AIRGLOW, -0.80)
        self.assertGreater(self.peak(midnight), 0.001)
        y, x = np.unravel_index(int(midnight.argmax()), midnight.shape[:2])
        red, green, blue = (float(midnight[y, x, c]) for c in range(3))
        self.assertGreater(green, red * 2.0, 'Airglow must read green')
        self.assertGreater(green, blue, 'Airglow is green-teal, not blue')
        self.assertLess(self.peak(self.image(AIRGLOW, -0.05)), 0.001,
                        'Airglow waits until the sky is dark')

    def test_overcast_suppresses_everything(self):
        clear = self.image(COMBINED, -0.10)
        overcast = self.image(OVERCAST, -0.10)
        self.assertGreater(self.peak(clear), 0.004)
        self.assertLess(self.peak(overcast), 1e-7,
                        'Cloud cover must suppress all three optics')


if __name__ == '__main__':
    unittest.main()
