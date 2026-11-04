"""GPU checks for the horizon reddening of stars.

The fixture calls `atmosphere` directly over a night-sky window. Stars are
additive, so the difference between the two builds isolates exactly the layer
under test. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 480, 320
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
STAR_NEW = ('vec3 starExtinction = mix(vec3(0.78,0.52,0.34), vec3(1.0),\n'
            '                                      smoothstep(0.10,0.44,ray.y));')
STAR_OLD = 'vec3 starExtinction = vec3(1.0);'


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert STAR_NEW in core
    if old:
        core = core.replace(STAR_NEW, STAR_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 0.25 * 6.2831853 * uv.x;
    float el = radians(4.0 + 70.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}''')


class StarExtinction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.old = cls.renderer.gl.compile(VERTEX, shader_source(old=True))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(-30.0)
        direction = [float(np.cos(elevation)) * 300.0,
                     float(np.sin(elevation)) * 300.0, 0.0]
        cls.renderer.uniform(program, 'sunPosition', direction)
        cls.renderer.uniform(program, 'shadowLightPosition', direction)
        cls.renderer.uniform(program, 'moonPosition', [-v for v in direction])
        cls.renderer.uniform(program, 'worldTime', 18000)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', 0.0)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', 0.0)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('star extinction')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    @classmethod
    def band(cls, data, low, high):
        elevation = 4.0 + 70.0 * (np.arange(H) + 0.5) / H
        rows = np.nonzero((elevation >= low) & (elevation <= high))[0]
        assert len(rows) > 5
        return data[rows, :, :3]

    def test_high_stars_are_unchanged(self):
        new = self.band(self.image(self.new), 30.0, 70.0)
        old = self.band(self.image(self.old), 30.0, 70.0)
        np.testing.assert_array_equal(new, old)

    def test_horizon_stars_lose_blue_light(self):
        new = self.band(self.image(self.new), 5.0, 20.0)
        old = self.band(self.image(self.old), 5.0, 20.0)
        mask = np.abs(new - old).max(axis=2) > 0.0
        self.assertGreater(int(mask.sum()), 40)
        before = old[mask]
        after = new[mask]
        lost_red = float(before[:, 0].sum() - after[:, 0].sum()) /                    float(before[:, 0].sum())
        lost_blue = float(before[:, 2].sum() - after[:, 2].sum()) /                     float(before[:, 2].sum())
        self.assertGreater(lost_blue, lost_red * 2.0)

    def test_horizon_stars_darken(self):
        new = self.band(self.image(self.new), 5.0, 20.0)
        old = self.band(self.image(self.old), 5.0, 20.0)
        self.assertGreater(float(old.mean()), float(new.mean()))

    def test_stars_stay_visible(self):
        new = self.band(self.image(self.new), 5.0, 20.0)
        old = self.band(self.image(self.old), 5.0, 20.0)
        self.assertGreater(float(np.abs(new - old).sum()), 0.0)
        self.assertGreater(float(new.max()), 0.5 * float(old.max()))

    def test_deterministic(self):
        a = self.image(self.new)
        b = self.image(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
