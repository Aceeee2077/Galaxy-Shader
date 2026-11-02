"""GPU checks for the airglow gravity-wave banding.

The fixture evaluates airglow() directly on a synthetic upper hemisphere with
AIRGLOW_RIPPLES compiled on and off. It measures band statistics rather than
absolute brightness, so the test stays independent of exposure.
"""
import re
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 180
ELEVATION_SPAN = 0.50
PROFILE_ROWS = np.s_[4:150]
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
OFF, ON = 0, 1


def fragment(ripples):
    common = expand(SHADERS / 'lib/common.glsl')
    common = re.sub(r'^\s*#define\s+AIRGLOW_RIPPLES\s+\S+',
                    f'#define AIRGLOW_RIPPLES {ripples}', common, flags=re.M)
    return ('#version 330 compatibility\n' + common +
            expand(SHADERS / 'lib/twilight_optics.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testAzimuth;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float elevation = uv.y * 0.50;
    vec3 ray = vec3(cos(elevation) * cos(testAzimuth), sin(elevation),
                    cos(elevation) * sin(testAzimuth));
    gl_FragColor = vec4(airglow(ray, normalize(testSun)), 1.0);
}''')


class AirglowRipplesRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.programs = {}
        for state in (OFF, ON):
            cls.programs[state] = cls.renderer.gl.compile(VERTEX, fragment(state))
        cls.renderer.bind_fbo([cls.renderer.final])
        for program in cls.programs.values():
            cls.renderer.call('glUseProgram', None, [U], program)
            cls.renderer.uniform(program, 'gbufferModelViewInverse',
                                 np.eye(4, dtype=np.float32))
            cls.renderer.uniform(program, 'testResolution', [W, H])
            cls.renderer.uniform(program, 'testSun', [0.0, -0.80, 1.0])

    @classmethod
    def tearDownClass(cls):
        for program in cls.programs.values():
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, state, azimuth=0.6, time=40.0, sun_height=-0.80):
        program = cls.programs[state]
        cls.renderer.call('glUseProgram', None, [U], program)
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        cls.renderer.uniform(program, 'testSun',
                             [horizontal, sun_height, 0.0])
        cls.renderer.uniform(program, 'testAzimuth', float(azimuth))
        cls.renderer.uniform(program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('airglow ripples')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def profile(image, column):
        return image[PROFILE_ROWS, column, 1].astype(np.float64)

    def test_deterministic(self):
        a = self.image(ON, azimuth=1.1, time=321.0)
        b = self.image(ON, azimuth=1.1, time=321.0)
        np.testing.assert_array_equal(a, b, 'Airglow must be frame-stable')

    def test_gravity_wave_bands_add_contrast(self):
        column = W // 2
        off = self.profile(self.image(OFF), column)
        on = self.profile(self.image(ON), column)
        # Remove the broad airglow layer envelope so only fine structure
        # competes: the ripple period is far shorter than the layer itself.
        window = 61
        smooth = np.ones(window) / window
        off_fine = off - np.convolve(off, smooth, mode='same')
        on_fine = on - np.convolve(on, smooth, mode='same')
        inner = np.s_[30:-30]
        off_contrast = float(off_fine[inner].std() / off.mean())
        on_contrast = float(on_fine[inner].std() / on.mean())
        self.assertGreater(on_contrast, off_contrast * 2.0,
                           'Ripples must add banding contrast to the layer')

        off_spec = np.abs(np.fft.rfft(off_fine[20:-20]))
        on_spec = np.abs(np.fft.rfft(on_fine[20:-20]))
        period_rows = 2.0 * np.pi / 46.0 / ELEVATION_SPAN * H
        band = int(round(len(off_spec) * 2.0 / period_rows))
        band_slice = np.s_[max(1, band - 1):band + 2]
        self.assertGreater(float(on_spec[band_slice].max()),
                           float(off_spec[band_slice].max()) * 1.6,
                           'The added structure must be periodic, not noise')

    def test_bands_bend_with_azimuth(self):
        first = self.profile(self.image(ON, azimuth=0.2), W // 2)
        second = self.profile(self.image(ON, azimuth=2.4), W // 2)
        first = (first - first.mean()) / first.std()
        second = (second - second.mean()) / second.std()
        self.assertLess(float(np.mean(np.abs(first - second))), 1.5,
                        'Band profiles must stay comparable in strength')
        self.assertGreater(float(np.mean(np.abs(first - second))), 0.35,
                           'The ripple phase must warp across azimuth')

    def test_only_at_night(self):
        self.assertLess(float(self.image(ON, sun_height=0.30).max()), 1e-7)
        self.assertLess(float(self.image(ON, sun_height=-0.05).max()), 0.0008)
        self.assertGreater(float(self.image(ON, sun_height=-0.80).max()), 0.001)

    def test_drift_is_slow_but_present(self):
        first = self.image(ON, azimuth=0.9, time=40.0)
        later = self.image(ON, azimuth=0.9, time=400.0)
        self.assertGreater(float(np.mean(np.abs(first - later))), 1e-7,
                           'The pattern must drift over several minutes')
        self.assertLess(float(np.mean(np.abs(first - later))), 0.05,
                        'Airglow drift must stay far slower than weather')


if __name__ == '__main__':
    unittest.main()
