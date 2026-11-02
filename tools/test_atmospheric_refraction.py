"""GPU checks for near-horizon atmospheric refraction of the sun and moon.

The sun fixture renders atmosphere(ray,true)-atmosphere(ray,false) in a
ten-degree window centred on a synthetic sun, so only the disk and its
night-side companions remain. The moon fixture samples moonSky() in a narrow
window. Both are compared against the same source with the option forced off.
Engineering checks, not Minecraft screenshots.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 320
SUN_HALF = 5.0
MOON_HALF = 4.0
SUN_THRESHOLD = 4.0
MOON_THRESHOLD = 0.4
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
WEIGHTS = np.array([0.2126, 0.7152, 0.0722], np.float32)


def with_option(source, value):
    return source.replace('#define ATMOSPHERIC_REFRACTION 1',
                          f'#define ATMOSPHERIC_REFRACTION {value}')


def sun_source(value):
    source = ('#version 330 compatibility\n#define DIMENSION 0\n' +
              expand(SHADERS / 'lib/common.glsl') +
              expand(SHADERS / 'lib/atmosphere.glsl') +
              '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 sun = normalize(testSun);
    vec3 helper = abs(sun.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(helper, sun));
    vec3 up = cross(sun, right);
    vec3 ray = normalize(sun + right * tan(uv.x * radians(5.0)) +
                         up * tan(uv.y * radians(5.0)));
    gl_FragColor = vec4(atmosphere(ray, true) - atmosphere(ray, false), 1.0);
}''')
    return with_option(source, value)


def moon_source(value):
    source = ('#version 330 compatibility\n#define DIMENSION 0\n' +
              expand(SHADERS / 'lib/common.glsl') +
              expand(SHADERS / 'lib/moon.glsl') +
              '''
uniform vec2 testResolution;
uniform vec3 testCenter;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 center = normalize(testCenter);
    vec3 helper = abs(center.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(center, helper));
    vec3 up = cross(right, center);
    vec3 ray = normalize(center + right * tan(uv.x * radians(4.0)) +
                         up * tan(uv.y * radians(4.0)));
    gl_FragColor = vec4(moonSky(ray, 1.0, 0.0), 1.0);
}''')
    return with_option(source, value)


def disk_stats(image, threshold):
    """Vertical and horizontal extents plus the vertical centroid, in pixels."""
    luminance = image @ WEIGHTS
    mask = luminance > threshold
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    if rows.size == 0 or cols.size == 0:
        raise AssertionError('No disk pixels above the threshold')
    weighted = np.where(mask, luminance, 0.0)
    centroid = float((weighted * np.arange(luminance.shape[0])[:, None]).sum() /
                     weighted.sum())
    return rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1, centroid


class AtmosphericRefractionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.sun_on = cls.renderer.gl.compile(VERTEX, sun_source(1))
        cls.sun_off = cls.renderer.gl.compile(VERTEX, sun_source(0))
        cls.moon_on = cls.renderer.gl.compile(VERTEX, moon_source(1))
        cls.moon_off = cls.renderer.gl.compile(VERTEX, moon_source(0))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.sun_on, cls.sun_off, cls.moon_on, cls.moon_off):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def sun_image(cls, program, elevation_degrees):
        elevation = np.radians(elevation_degrees)
        sun = np.array([np.cos(elevation), np.sin(elevation), 0.0], np.float32)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testSun', sun)
        cls.renderer.uniform(program, 'sunPosition', sun * 100.0)
        cls.renderer.uniform(program, 'moonPosition', -sun * 100.0)
        cls.renderer.full_screen()
        cls.renderer.check('atmospheric refraction')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @classmethod
    def moon_image(cls, program, elevation_degrees):
        elevation = np.radians(elevation_degrees)
        center = np.array([np.cos(elevation), np.sin(elevation), 0.0], np.float32)
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testCenter', center)
        cls.renderer.uniform(program, 'sunPosition', [100.0, 0.0, 0.0])
        cls.renderer.uniform(program, 'moonPosition', center * 100.0)
        cls.renderer.uniform(program, 'moonPhase', 0)
        cls.renderer.full_screen()
        cls.renderer.check('refracted moon')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_deterministic(self):
        first = self.sun_image(self.sun_on, 2.0)
        second = self.sun_image(self.sun_on, 2.0)
        np.testing.assert_array_equal(first, second,
                                      'Refraction must be stable between frames')

    def test_low_sun_is_vertically_flattened(self):
        off = disk_stats(self.sun_image(self.sun_off, 2.0), SUN_THRESHOLD)
        on = disk_stats(self.sun_image(self.sun_on, 2.0), SUN_THRESHOLD)
        self.assertLess(on[0], off[0] * 0.96,
                        'The low sun must compress vertically')
        self.assertGreater(on[0], off[0] * 0.85,
                           'The disk must stay recognisably round')
        self.assertLess(abs(on[1] - off[1]), max(2, int(off[1] * 0.02)),
                        'Refraction must not change the horizontal diameter')

    def test_low_sun_is_lifted(self):
        off = disk_stats(self.sun_image(self.sun_off, 2.0), SUN_THRESHOLD)
        on = disk_stats(self.sun_image(self.sun_on, 2.0), SUN_THRESHOLD)
        pixels_per_degree = H / (2.0 * SUN_HALF)
        lift = (on[2] - off[2]) / pixels_per_degree
        self.assertGreater(lift, 0.15,
                           'The apparent disk must rise above the true centre')
        self.assertLess(lift, 0.60,
                        'The lift must stay within the physical limit')

    def test_high_sun_is_unchanged(self):
        off = self.sun_image(self.sun_off, 45.0)
        on = self.sun_image(self.sun_on, 45.0)
        np.testing.assert_array_equal(on, off,
                                      'High sun must keep the plain disk path')

    def test_low_moon_is_flattened_and_lifted(self):
        off = disk_stats(self.moon_image(self.moon_off, 2.0), MOON_THRESHOLD)
        on = disk_stats(self.moon_image(self.moon_on, 2.0), MOON_THRESHOLD)
        self.assertLess(on[0], off[0] * 0.97,
                        'The low moon must compress vertically')
        self.assertGreater(on[0], off[0] * 0.85,
                           'The moon must stay recognisably round')
        self.assertLess(abs(on[1] - off[1]), max(2, int(off[1] * 0.02)),
                        'Refraction must not change the horizontal diameter')
        self.assertGreater(on[2] - off[2], 2.0,
                           'The apparent moon must rise above the true centre')


if __name__ == '__main__':
    unittest.main()
