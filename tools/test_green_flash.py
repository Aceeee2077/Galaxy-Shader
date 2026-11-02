"""GPU checks for the analytic green flash on the solar limb.

The fixture samples the authored function in a small angular window around the
sun. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 200, 200
HALF_DEGREES = 5.0
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def frame(elevation):
    sun = np.array([np.cos(elevation), np.sin(elevation), 0.0])
    helper = np.array([0.0, 0.0, 1.0]) if abs(sun[1]) > 0.98 else np.array([0.0, 1.0, 0.0])
    right = np.cross(sun, helper)
    right /= np.linalg.norm(right)
    up = np.cross(right, sun)
    return sun, right, up


def ray_grid(elevation):
    sun, right, up = frame(elevation)
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    dx = np.tan(np.deg2rad((u * 2.0 - 1.0) * HALF_DEGREES))[None, :]
    dy = np.tan(np.deg2rad((v * 2.0 - 1.0) * HALF_DEGREES))[:, None]
    rays = sun[None, None, :] + right[None, None, :] * dx[:, :, None] + \
        up[None, None, :] * dy[:, :, None]
    return rays / np.linalg.norm(rays, axis=2, keepdims=True)


class GreenFlashRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/green_flash.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float dx = radians((uv.x * 2.0 - 1.0) * 5.0);
    float dy = radians((uv.y * 2.0 - 1.0) * 5.0);
    vec3 sun = normalize(testSun);
    vec3 helper = abs(sun.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(sun, helper));
    vec3 up = cross(right, sun);
    vec3 ray = normalize(sun + right * tan(dx) + up * tan(dy));
    gl_FragColor = vec4(greenFlash(ray, sun, testVisibility, 2.0), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        # Signed offsets in the solar disk frame, in degrees.
        u = (np.arange(W) + 0.5) / W
        v = (np.arange(H) + 0.5) / H
        cls.dx = np.broadcast_to((u * 2.0 - 1.0) * HALF_DEGREES, (H, W))
        cls.dy = np.broadcast_to(((v * 2.0 - 1.0) * HALF_DEGREES)[:, None], (H, W))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, elevation=0.01, visibility=1.0):
        cls.renderer.uniform(cls.program, 'testSun',
                             [np.cos(elevation), np.sin(elevation), 0.0])
        cls.renderer.uniform(cls.program, 'testVisibility', visibility)
        cls.renderer.full_screen()
        cls.renderer.check('green flash')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Green flash must be stable')

    def test_rim_sits_on_the_upper_limb(self):
        image = self.image()
        rim = self.peak(image, (np.abs(self.dx) < 1.2) &
                        (self.dy > 1.2) & (self.dy < 2.8))
        centre = self.peak(image, (np.abs(self.dx) < 1.0) &
                          (np.abs(self.dy) < 1.0))
        far = self.peak(image, self.dy > 3.6)
        self.assertGreater(rim, 0.30, 'The limb must flash green')
        self.assertLess(centre, rim * 0.1, 'No flash inside the disk')
        self.assertLess(far, rim * 0.05, 'No flash away from the limb')

    def test_green_dominates_the_limb(self):
        image = self.image()
        mask = (np.abs(self.dx) < 1.2) & (self.dy > 1.4) & (self.dy < 2.6)
        colour = image[mask].max(axis=0)
        self.assertGreater(colour[1], colour[0] * 2.0)
        self.assertGreater(colour[1], colour[2] * 1.02)

    def test_high_sun_and_below_horizon_gate(self):
        self.assertLess(float(self.image(0.20).max()), 1e-7)
        self.assertLess(float(self.image(-0.10).max()), 1e-7)

    def test_visibility_suppresses_the_flash(self):
        self.assertLess(float(self.image(visibility=0.0).max()), 1e-7)

    def test_lower_half_stays_dark(self):
        image = self.image()
        lower = self.peak(image, (np.abs(self.dx) < 1.2) &
                          (self.dy < -1.2) & (self.dy > -2.8))
        upper = self.peak(image, (np.abs(self.dx) < 1.2) &
                          (self.dy > 1.2) & (self.dy < 2.8))
        self.assertGreater(upper, lower * 5.0)


if __name__ == '__main__':
    unittest.main()
