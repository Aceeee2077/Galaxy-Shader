"""GPU checks for the low-sun elongation of solar parhelia.

The fixture samples `iceHalo` around the right-hand dog of a low sun. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 160
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW = '''        float dogVertical = mix(6.2 * deg, 2.5 * deg,
                                smoothstep(0.02, 0.20, lightDir.y));'''
OLD = '        float dogVertical = 2.5 * deg;'


def halo_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(19.0 + 6.0 * uv.x);
    float el = radians(0.0 + 22.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(iceHalo(ray, normalize(testSun), 1.0, vec3(1.0),
                                0.0), 1.0);
}''')


class DogPillarRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        source = halo_source()
        assert NEW in source
        cls.new = cls.renderer.gl.compile(VERTEX, source)
        cls.old = cls.renderer.gl.compile(VERTEX, source.replace(NEW, OLD))
        cls.hidden = cls.renderer.gl.compile(
            VERTEX, source.replace('1.0, vec3(1.0)', '0.0, vec3(1.0)'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old, cls.hidden):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, sun_deg):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(sun_deg)),
                              np.sin(np.deg2rad(sun_deg)), 0.0])
        cls.renderer.full_screen()
        cls.renderer.check('dog pillar')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def dog_column(self, image, sun_deg, az_deg):
        az = 19.0 + 6.0 * (np.arange(W) + 0.5) / W
        col = int(np.argmin(np.abs(az - az_deg)))
        return image[:, col].mean(axis=1)

    def centre_row(self, sun_deg):
        # The dog centre sits at the sun's elevation; the grid is 0..22 deg.
        return int(np.argmin(np.abs((np.arange(H) + 0.5) / H * 22.0 - sun_deg)))

    def test_low_sun_smear_is_taller(self):
        image = self.image(self.new, 3.0)
        row = self.centre_row(3.0)
        column = self.dog_column(image, 3.0, 21.8)
        peak = column[row]
        above = column[min(row + int(H * 4.0 / 22.0), H - 1)]
        self.assertGreater(above, peak * 0.25)

    def test_high_sun_matches_the_previous_dog(self):
        new = self.image(self.new, 12.0)
        old = self.image(self.old, 12.0)
        np.testing.assert_allclose(new, old, atol=2e-4)

    def test_horizontal_width_is_unchanged(self):
        row = self.centre_row(3.0)
        az = 19.0 + 6.0 * (np.arange(W) + 0.5) / W
        centre_col = int(np.argmin(np.abs(az - 21.8)))
        side_col = int(np.argmin(np.abs(az - (21.8 + 3.0))))
        ratios = []
        for program in (self.new, self.old):
            image = self.image(program, 3.0)
            centre = float(image[row, centre_col].mean())
            side = float(image[row, side_col].mean())
            ratios.append(side / max(centre, 1e-12))
        self.assertGreater(ratios[0], 0.0)
        self.assertAlmostEqual(ratios[0], ratios[1], places=3)

    def test_zero_visibility_is_black(self):
        data = self.image(self.hidden, 3.0)
        self.assertLess(float(np.abs(data).max()), 1e-6)

    def test_deterministic(self):
        a = self.image(self.new, 3.0)
        b = self.image(self.new, 3.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
