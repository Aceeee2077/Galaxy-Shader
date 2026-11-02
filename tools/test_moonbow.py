"""GPU checks for the analytic lunar rainbow.

The fixture samples the authored moonbow function over a synthetic sky dome. It
is an engineering check, not a Minecraft screenshot or a Mie scattering model.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 120
MAX_ELEVATION = 1.00
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def ray_grid():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    azimuth = (u * 2.0 - 1.0) * np.pi
    elevation = v * MAX_ELEVATION
    cos_e = np.cos(elevation)[:, None]
    return np.stack([cos_e * np.cos(azimuth)[None, :],
                     np.sin(elevation)[:, None] * np.ones_like(u)[None, :],
                     cos_e * np.sin(azimuth)[None, :]], axis=-1)


def moon_vector(elevation):
    # Place the moon opposite the panorama centre, so the anti-lunar point and
    # the arc sit in the middle of the sampled dome.
    return np.array([-np.cos(elevation), np.sin(elevation), 0.0])


class MoonbowRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/moonbow.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testMoon;
uniform float testLit;
uniform float testMoisture;
uniform float testNight;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.00;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = moonbow(ray, normalize(testMoon), testLit, testMoisture,
                         testNight, testOvercast);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.moon = moon_vector(np.deg2rad(25.0))
        cls.rays_to_anti = np.degrees(
            np.arccos(np.clip(cls.rays @ (-cls.moon), -1.0, 1.0)))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, lit=1.0, moisture=1.0, night=1.0, overcast=0.0,
              elevation=25.0):
        moon = moon_vector(np.deg2rad(elevation))
        cls.renderer.uniform(cls.program, 'testMoon', moon.tolist())
        cls.renderer.uniform(cls.program, 'testLit', lit)
        cls.renderer.uniform(cls.program, 'testMoisture', moisture)
        cls.renderer.uniform(cls.program, 'testNight', night)
        cls.renderer.uniform(cls.program, 'testOvercast', overcast)
        cls.renderer.full_screen()
        cls.renderer.check('moonbow')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def test_deterministic(self):
        a = self.image()
        b = self.image()
        np.testing.assert_array_equal(a, b, 'Moonbow must be stable')

    def test_arc_sits_at_42_degrees_from_the_anti_lunar_point(self):
        image = self.image()
        arc = self.peak(image, np.abs(self.rays_to_anti - 42.0) < 1.0)
        inner = self.peak(image, np.abs(self.rays_to_anti - 30.0) < 2.0)
        outer = self.peak(image, np.abs(self.rays_to_anti - 52.0) < 2.0)
        self.assertGreater(arc, 0.01, 'The anti-lunar arc must be visible')
        self.assertLess(inner, 1e-7, 'No light inside the bow')
        self.assertLess(outer, 1e-7, 'No light outside the bow')

    def test_daylight_gate(self):
        self.assertLess(float(self.image(night=0.0).max()), 1e-7)

    def test_new_moon_cannot_draw_a_moonbow(self):
        new = self.image(lit=0.0)
        full = self.image(lit=1.0)
        self.assertLess(float(new.max()), 1e-7)
        self.assertGreater(float(full.max()), float(new.max()))

    def test_dry_air_removes_the_arc_and_cloud_reduces_it(self):
        dry = self.image(moisture=0.0)
        clear = self.image(overcast=0.0)
        cloudy = self.image(overcast=1.0)
        self.assertLess(float(dry.max()), 1e-7)
        self.assertLess(float(cloudy.max()), float(clear.max()) * 0.4)

    def test_arc_stays_on_the_anti_lunar_side(self):
        image = self.image()
        lunar_side = np.degrees(
            np.arccos(np.clip(self.rays @ self.moon, -1.0, 1.0)))
        self.assertLess(self.peak(image, np.abs(lunar_side - 42.0) < 2.0),
                        1e-7, 'Moonbow must not appear around the moon')


if __name__ == '__main__':
    unittest.main()
