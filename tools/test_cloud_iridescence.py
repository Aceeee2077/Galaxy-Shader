"""GPU checks for thin-cloud iridescence near the sun.

The fixture builds a polar grid of rays around a synthetic sun and evaluates
cloudIridescence() directly. It checks angular confinement, pastel colour,
patchiness and weather/day gates.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 320, 320
MAX_OFFSET = 0.70
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


class CloudIridescenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/cloud_iridescence.glsl') +
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
    vec2 offset = uv * 0.70;
    float angle = length(offset);
    vec3 tangent = angle > 1e-5 ? normalize(east * offset.x + north * offset.y)
                                : east;
    vec3 ray = normalize(sun * cos(angle) + tangent * sin(angle));
    gl_FragColor = vec4(cloudIridescence(ray, sun, testDay, testOvercast), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testSun',
                             [0.3, 0.5, 0.8])
        cls.renderer.uniform(cls.program, 'testDay', 1.0)
        cls.renderer.uniform(cls.program, 'testOvercast', 0.0)
        axis = np.linspace(-1.0, 1.0, W)
        cls.offset = np.sqrt(axis[None, :] ** 2 + axis[:, None] ** 2) * MAX_OFFSET

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, day=1.0, overcast=0.0, time=90.0):
        cls.renderer.uniform(cls.program, 'testDay', day)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.uniform(cls.program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('cloud iridescence')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        a = self.image(time=321.0)
        b = self.image(time=321.0)
        np.testing.assert_array_equal(a, b, 'Iridescence must be frame-stable')

    def test_confined_near_the_sun(self):
        image = self.image()
        core = self.offset < 0.30
        self.assertGreater(float(image[core].max()), 0.004)
        outside = self.offset > 0.66
        self.assertLess(float(image[outside].max()), 1e-7,
                        'No fringes beyond the angular window')

    def test_pastel_fringes_and_broken_veil(self):
        image = self.image()
        bright = image.max(axis=2) > 1e-5
        self.assertGreater(int(bright.sum()), 3000)
        ring = (self.offset > 0.15) & (self.offset < 0.25) & bright
        chroma = image[ring].max(axis=1) - image[ring].min(axis=1)
        self.assertGreater(float(chroma.mean()), 0.004,
                           'Fringes must carry pastel colour, not grey')
        luminance = image.max(axis=2)[bright]
        self.assertGreater(float(luminance.std()),
                           float(luminance.mean()) * 0.30,
                           'The veil must be broken, not a smooth ring')

    def test_day_and_cloud_gates(self):
        self.assertLess(float(self.image(day=0.0).max()), 1e-7)
        self.assertLess(float(self.image(overcast=1.0).max()), 1e-7)

    def test_drift_is_slow_but_present(self):
        first = self.image(time=90.0)
        later = self.image(time=500.0)
        self.assertGreater(float(np.abs(first - later).mean()), 1e-7)
        self.assertLess(float(np.abs(first - later).mean()), 0.02)


if __name__ == '__main__':
    unittest.main()
