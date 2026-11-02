"""GPU checks for the broad Bishop's-ring dust aureole.

The fixture samples bishopsRing() on a polar grid around a synthetic sun. It
checks radius, softness, warm-to-cool colour and the day/weather gates.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 320, 320
MAX_OFFSET = 0.88
DEG = np.pi / 180.0
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


class BishopsRingRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/bishops_ring.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testDay;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 sun = normalize(testSun);
    vec3 ref = abs(sun.y) < 0.95 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 east = normalize(cross(ref, sun));
    vec3 north = cross(sun, east);
    vec2 offset = uv * 0.88;
    float angle = length(offset);
    vec3 tangent = angle > 1e-5 ? normalize(east * offset.x + north * offset.y)
                                : east;
    vec3 ray = normalize(sun * cos(angle) + tangent * sin(angle));
    gl_FragColor = vec4(bishopsRing(ray, sun, testDay, testOvercast), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testSun', [0.3, 0.5, 0.8])
        cls.renderer.uniform(cls.program, 'testDay', 1.0)
        cls.renderer.uniform(cls.program, 'testOvercast', 0.0)
        axis = np.linspace(-1.0, 1.0, W)
        cls.angle = np.sqrt(axis[None, :] ** 2 + axis[:, None] ** 2) * MAX_OFFSET

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, day=1.0, overcast=0.0):
        cls.renderer.uniform(cls.program, 'testDay', day)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.full_screen()
        cls.renderer.check("Bishop's ring")
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def radial_profile(self, image):
        centres = []
        values = []
        for low in np.arange(0.02, 0.84, 0.01):
            mask = (self.angle >= low) & (self.angle < low + 0.01)
            if mask.any():
                centres.append(low + 0.005)
                values.append(float(image[mask].mean()))
        return np.array(centres), np.array(values)

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, "Bishop's ring must be stable")

    def test_annulus_radius_and_softness(self):
        centres, profile = self.radial_profile(self.image())
        peak = int(profile.argmax())
        self.assertGreater(float(profile[peak]), 0.004)
        degrees = centres[peak] / DEG
        self.assertTrue(20.0 < degrees < 28.0,
                        f'Peak radius {degrees:.1f} degrees is too narrow')
        half = profile[peak] * 0.5
        above = np.where(profile >= half)[0]
        width = (centres[above[-1]] - centres[above[0]]) / DEG
        self.assertGreater(width, 8.0,
                           'Bishop\'s ring must stay a broad aureole')

    def test_inner_is_warm_outer_is_cool(self):
        image = self.image()
        inner = image[(self.angle > 18 * DEG) & (self.angle < 22 * DEG)]
        outer = image[(self.angle > 30 * DEG) & (self.angle < 35 * DEG)]
        inner_mean = inner.mean(axis=0)
        outer_mean = outer.mean(axis=0)
        self.assertGreater(float(inner_mean[0]), float(inner_mean[2]) * 1.05,
                           'Inner edge must be dust-warm')
        self.assertGreater(float(outer_mean[2]), float(outer_mean[0]) * 1.05,
                           'Outer skirt must be pale blue')

    def test_day_and_weather_gates(self):
        self.assertLess(float(self.image(day=0.0).max()), 1e-7)
        self.assertLess(float(self.image(overcast=1.0).max()), 1e-7)
        sunless = self.image()
        self.assertGreater(float(sunless.max()), 0.004)

    def test_confined_away_from_the_sun_disk(self):
        image = self.image()
        core = self.angle < 12 * DEG
        ring = (self.angle > 20 * DEG) & (self.angle < 28 * DEG)
        self.assertLess(float(image[core].max()), float(image[ring].max()) * 0.2,
                        'The sun disk must stay clear of the ring')
        self.assertLess(float(image[self.angle > 48 * DEG].max()), 1e-7,
                        'No aureole outside the outer skirt')


if __name__ == '__main__':
    unittest.main()
