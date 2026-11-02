"""GPU checks for the meteor persistent train.

The fixture samples a strip around one authored meteor path. It is an
engineering check, not a Minecraft screenshot or a chemical model.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 900, 160
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
HEAD = np.array([0.2, 0.35, -0.9])
HEAD = HEAD / np.linalg.norm(HEAD)
TAIL = HEAD - np.array([-0.10, -0.26, 0.06]) * 0.28
TAIL = TAIL / np.linalg.norm(TAIL)


def strip_grid():
    u = 0.01 + 0.98 * (np.arange(W) + 0.5) / W
    v = -0.09 + 0.18 * (np.arange(H) + 0.5) / H
    path_dir = (HEAD - TAIL) / np.linalg.norm(HEAD - TAIL)
    in_plane = HEAD - path_dir * np.dot(HEAD, path_dir)
    in_plane /= np.linalg.norm(in_plane)
    a0 = np.arccos(np.clip(np.dot(TAIL, path_dir), -1.0, 1.0))
    a1 = np.arccos(np.clip(np.dot(HEAD, path_dir), -1.0, 1.0))
    a = a0 + (a1 - a0) * u
    base = (path_dir[None, :] * np.cos(a)[:, None] +
            in_plane[None, :] * np.sin(a)[:, None])
    side = np.cross(base, path_dir[None, :])
    side /= np.linalg.norm(side, axis=1, keepdims=True)
    rays = base[:, None, :] * np.cos(v)[None, :, None] + \
        side[:, None, :] * np.sin(v)[None, :, None]
    rays /= np.linalg.norm(rays, axis=-1, keepdims=True)
    return np.transpose(rays, (1, 0, 2))


class MeteorTrainRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/meteor_train.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testHead;
uniform vec3 testTail;
uniform float testLife;
uniform float testSeed;
uniform float testTime;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 head = normalize(testHead);
    vec3 tail = normalize(testTail);
    vec3 pathDir = normalize(head - tail);
    vec3 inPlane = normalize(head - pathDir * dot(head, pathDir));
    float a0 = acos(clamp(dot(tail, pathDir), -1.0, 1.0));
    float a1 = acos(clamp(dot(head, pathDir), -1.0, 1.0));
    float a = mix(a0, a1, uv.x);
    vec3 base = pathDir * cos(a) + inPlane * sin(a);
    vec3 side = normalize(cross(base, pathDir));
    float b = mix(-0.09, 0.09, uv.y);
    vec3 ray = normalize(base * cos(b) + side * sin(b));
    gl_FragColor = vec4(meteorTrain(ray, head, tail, testLife,
                                    testSeed, testTime), 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.renderer.uniform(cls.program, 'testHead', HEAD.tolist())
        cls.renderer.uniform(cls.program, 'testTail', TAIL.tolist())
        cls.rays = strip_grid()

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, life=1.0, seed=0.37, time=0.0):
        cls.renderer.uniform(cls.program, 'testLife', life)
        cls.renderer.uniform(cls.program, 'testSeed', seed)
        cls.renderer.uniform(cls.program, 'testTime', time)
        cls.renderer.full_screen()
        cls.renderer.check('meteor train')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'The train must be stable')

    def test_train_lies_on_the_meteor_path(self):
        image = self.image()
        path_dir = (HEAD - TAIL) / np.linalg.norm(HEAD - TAIL)
        plane = np.cross(HEAD, path_dir)
        plane /= np.linalg.norm(plane)
        cross = np.abs(np.arcsin(np.clip(self.rays @ plane, -1.0, 1.0)))
        near = cross < np.deg2rad(0.5)
        far = cross > np.deg2rad(4.0)
        self.assertGreater(float(image[near].max()), 0.01,
                           'The train must be visible on the path')
        self.assertLess(float(image[far].max()), 1e-7,
                        'Nothing outside the path plane')

    def test_train_is_narrow(self):
        image = self.image()
        path_dir = (HEAD - TAIL) / np.linalg.norm(HEAD - TAIL)
        plane = np.cross(HEAD, path_dir)
        plane /= np.linalg.norm(plane)
        cross = np.abs(np.arcsin(np.clip(self.rays @ plane, -1.0, 1.0)))
        centre = image[cross < np.deg2rad(0.4)]
        side = image[cross > np.deg2rad(2.95)]
        self.assertGreater(float(centre.max()), 0.01)
        self.assertLess(float(side.max()), 1e-7)

    def test_knots_alternate_along_the_train(self):
        image = self.image().mean(axis=2)
        path_dir = (HEAD - TAIL) / np.linalg.norm(HEAD - TAIL)
        plane = np.cross(HEAD, path_dir)
        plane /= np.linalg.norm(plane)
        cross = np.abs(np.arcsin(np.clip(self.rays @ plane, -1.0, 1.0)))
        middle = int(np.argmin(cross[:, W // 2]))
        profile = image[middle]
        self.assertGreater(float(profile.std()), float(profile.mean()) * 0.05,
                           'The train should break into knots')
        smooth = np.convolve(profile, np.ones(7) / 7.0, mode='valid')
        peaks = np.sum((smooth[1:-1] >= smooth[:-2]) &
                       (smooth[1:-1] > smooth[2:]))
        self.assertGreaterEqual(int(peaks), 3, 'Several knots must survive')
        early, late = float(profile[:60].max()), float(profile[-60:].max())
        self.assertGreater(float(profile[400:500].max()),
                           max(early, late) * 1.2,
                           'The train is brightest around the middle')

    def test_life_gate_and_scaling(self):
        self.assertEqual(float(self.image(life=0.0).max()), 0.0)
        weak = float(self.image(life=0.2).max())
        strong = float(self.image(life=0.8).max())
        self.assertGreater(strong, weak * 2.5,
                           'Train brightness follows its life envelope')


if __name__ == '__main__':
    unittest.main()
