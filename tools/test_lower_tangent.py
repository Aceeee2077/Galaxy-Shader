"""GPU checks for the lower tangent arc of the 22-degree halo.

The fixture samples the authored halo function over a synthetic sky dome. It is
an engineering check, not a Minecraft screenshot or a scattering simulation.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 120
MAX_ELEVATION = 1.30
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


def light_vector(elevation):
    return np.array([np.cos(elevation), np.sin(elevation), 0.0])


class LowerTangentRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                    expand(SHADERS / 'lib/common.glsl') +
                    expand(SHADERS / 'lib/ice_halo.glsl') +
                    '''
uniform vec2 testResolution;
uniform vec3 testLight;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.30;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 value = iceHalo(ray, normalize(testLight), testVisibility,
                         vec3(1.0), 0.0);
    gl_FragColor = vec4(value, 1.0);
}''')
        cls.program = cls.renderer.gl.compile(VERTEX, fragment)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], cls.program)
        cls.renderer.uniform(cls.program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(cls.program, 'testResolution', [W, H])
        cls.rays = ray_grid()
        cls.elevation = np.degrees(np.arcsin(np.clip(cls.rays[:, :, 1], -1.0, 1.0)))
        cls.azimuth = np.abs(np.degrees(np.arctan2(cls.rays[:, :, 2],
                                                  cls.rays[:, :, 0])))

    @classmethod
    def tearDownClass(cls):
        cls.renderer.gl.delete_program(cls.program)
        cls.renderer.close()

    @classmethod
    def image(cls, sun_elevation_deg, visibility=1.0):
        rad = np.deg2rad(sun_elevation_deg)
        cls.renderer.uniform(cls.program, 'testLight',
                             light_vector(rad).tolist())
        cls.renderer.uniform(cls.program, 'testVisibility', visibility)
        cls.renderer.full_screen()
        cls.renderer.check('lower tangent arc')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def peak(image, mask):
        return float(image[mask].max()) if mask.any() else 0.0

    def ring_band(self, sun_deg, theta_deg, side=False):
        light = light_vector(np.deg2rad(sun_deg))
        theta = np.degrees(np.arccos(np.clip(self.rays @ light, -1.0, 1.0)))
        if side:
            near_axis = (self.azimuth > 20.0) & (self.azimuth < 30.0)
        else:
            # The same circle also crosses the upper tangent cap; keep only the
            # half below the sun so the lower arc is measured alone.
            near_axis = (self.azimuth < 8.0) & (self.elevation < sun_deg - 15.0)
        return (np.abs(theta - theta_deg) < 1.5) & near_axis

    def test_visible_below_a_high_sun(self):
        # The 22-degree ring runs through the band in every case; the arc is
        # the extra brightness directly below a high sun.
        image = self.image(40.0)
        below = self.peak(image, self.ring_band(40.0, 22.0))
        ring = self.peak(image, self.ring_band(40.0, 22.0, side=True))
        self.assertGreater(below, ring * 1.25)

    def test_gated_off_for_a_low_sun(self):
        image = self.image(25.0)
        below = self.peak(image, self.ring_band(25.0, 22.0))
        ring = self.peak(image, self.ring_band(25.0, 22.0, side=True))
        self.assertLess(abs(below - ring), 2.0e-4)

    def test_fades_away_from_the_ring(self):
        image = self.image(40.0)
        centre = self.peak(image, self.ring_band(40.0, 22.0))
        far = self.peak(image, self.ring_band(40.0, 28.0))
        self.assertLess(far, centre * 0.5)

    def test_zero_visibility_is_black(self):
        image = self.image(40.0, visibility=0.0)
        self.assertLess(float(image.max()), 1e-7)

    def test_deterministic(self):
        a = self.image(40.0)
        b = self.image(40.0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
