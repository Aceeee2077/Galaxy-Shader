"""GPU checks for the comet anti-tail.

The fixture samples the authored sunward spike over a synthetic sky. It is an
engineering check, not a Minecraft screenshot or an orbit calculation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 720, 480
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
HEAD = np.array([-0.35, 0.30, -0.88])
HEAD = HEAD / np.linalg.norm(HEAD)
TAIL = np.array([0.30, -0.55, 0.35])
TAIL = TAIL / np.linalg.norm(TAIL)


def ray_grid():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    azimuth = (u * 2.0 - 1.0) * np.pi
    elevation = v * 1.20
    cos_e = np.cos(elevation)[:, None]
    return np.stack([cos_e * np.cos(azimuth)[None, :],
                     np.sin(elevation)[:, None] * np.ones_like(u)[None, :],
                     cos_e * np.sin(azimuth)[None, :]], axis=-1)


class CometAntitailRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/noise.glsl') +
                    expand(SHADERS / 'lib/comet_antitail.glsl') +
                    '''
uniform vec2 testResolution;
uniform float testAmount;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.20;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(cometAntitail(ray, testAmount), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, amount=1.0):
        cls.renderer.uniform(cls.program, 'testAmount', amount)
        cls.renderer.full_screen()
        cls.renderer.check('comet anti-tail')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def angle_to(self, direction):
        return np.arccos(np.clip(self.rays @ direction, -1.0, 1.0))

    def spike_distance(self):
        """Cross-track angle from the sunward spike axis at the comet head.

        Rays behind the head or far out in azimuth report infinity so they
        cannot satisfy a "near the spike" mask merely by sitting close to the
        head in absolute angular distance.
        """
        along_dir = -TAIL - HEAD * np.dot(-TAIL, HEAD)
        along_dir /= np.linalg.norm(along_dir)
        cross_dir = np.cross(HEAD, along_dir)
        cos_head = np.clip(self.rays @ HEAD, -1.0, 1.0)
        tangent = self.rays - HEAD[None, None, :] * cos_head[..., None]
        tangent /= np.maximum(np.linalg.norm(tangent, axis=-1, keepdims=True),
                              1e-6)
        across = np.abs(np.arcsin(np.clip(tangent @ cross_dir, -1.0, 1.0)))
        behind = (tangent @ along_dir) <= 0.0
        return np.where(behind, np.inf, across)

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'The anti-tail must be stable')

    def test_spike_starts_at_the_head_and_runs_sunward(self):
        image = self.image()
        near = self.angle_to(HEAD)
        spike = self.spike_distance()
        along = ((spike < np.deg2rad(1.0)) & (near > np.deg2rad(1.5)) &
                 (near < np.deg2rad(18.0)))
        off = ((spike > np.deg2rad(6.0)) & (near > np.deg2rad(1.5)) &
               (near < np.deg2rad(18.0)))
        self.assertGreater(float(image[along].max()), 0.02,
                           'The sunward spike must be visible')
        self.assertLess(float(image[off].max()), 1e-7,
                        'Nothing away from the spike axis')

    def test_spike_is_narrow(self):
        image = self.image()
        near = self.angle_to(HEAD)
        spike = self.spike_distance()
        axis = ((near > np.deg2rad(4.0)) & (near < np.deg2rad(14.0)))
        centre = image[axis & (spike < np.deg2rad(0.7))]
        side = image[axis & (spike > np.deg2rad(3.0))]
        self.assertGreater(float(centre.max()), 0.02)
        self.assertLess(float(side.max()), 1e-7)

    def test_spike_fades_with_distance(self):
        image = self.image().mean(axis=2)
        spike = self.spike_distance()
        near = self.angle_to(HEAD)
        close = float(image[(spike < np.deg2rad(0.9)) &
                            (near > np.deg2rad(1.5)) &
                            (near < np.deg2rad(4.5))].max())
        far = float(image[(spike < np.deg2rad(0.9)) &
                          (near > np.deg2rad(6.5)) &
                          (near < np.deg2rad(8.7))].max())
        self.assertGreater(close, far * 1.5)

    def test_amount_gate(self):
        self.assertEqual(float(self.image(amount=0.0).max()), 0.0)


if __name__ == '__main__':
    unittest.main()
