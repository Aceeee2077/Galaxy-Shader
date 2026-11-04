"""GPU checks for the anthelion spot on the parhelic circle.

The fixture samples `iceHaloCompanions` over the sky around the anti-solar
point. It is an engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW = '''float strength = 0.35 + 0.65 * nearSun + 0.45 * parhelia +
                             0.34 * anthelion;'''
OLD = 'float strength = 0.35 + 0.65 * nearSun + 0.45 * parhelia;'


def source(az_start, az_span):
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo_extras.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(''' + str(az_start) + ''' + ''' + str(az_span) +
            ''' * uv.x);
    float el = radians(15.0 + 14.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(iceHaloCompanions(ray, normalize(testSun),
                                          testVisibility), 1.0);
}''')


class AnthelionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        near = source(-60.0, 120.0)
        far = source(100.0, 160.0)
        for text in (near, far):
            assert NEW in text
        cls.new_near = cls.renderer.gl.compile(VERTEX, near)
        cls.old_near = cls.renderer.gl.compile(VERTEX, near.replace(NEW, OLD))
        cls.new_far = cls.renderer.gl.compile(VERTEX, far)
        cls.old_far = cls.renderer.gl.compile(VERTEX, far.replace(NEW, OLD))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new_near, cls.old_near, cls.new_far,
                        cls.old_far):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, visibility=1.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testVisibility', float(visibility))
        # Sun at 22 degrees toward azimuth 0; the far window looks at 180.
        cls.renderer.uniform(program, 'testSun',
                             [np.cos(np.deg2rad(22.0)),
                              np.sin(np.deg2rad(22.0)), 0.0])
        cls.renderer.full_screen()
        cls.renderer.check('anthelion')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_sunward_sky_is_unchanged(self):
        new = self.image(self.new_near)
        old = self.image(self.old_near)
        np.testing.assert_allclose(new[:, :, :3], old[:, :, :3], atol=2e-4)

    def test_antisolar_point_is_brighter(self):
        new = self.image(self.new_far)
        old = self.image(self.old_far)
        rows = new.shape[0]
        centre = new[rows // 2, new.shape[1] // 2, :3]
        previous = old[rows // 2, new.shape[1] // 2, :3]
        self.assertGreater(float(centre.max()),
                           float(previous.max()) * 1.3)

    def test_spot_is_local_to_the_antisolar_azimuth(self):
        new = self.image(self.new_far)
        old = self.image(self.old_far)
        rows = new.shape[0]
        middle = new[rows // 2, :, :3]
        mask = np.abs(np.arange(W) - W // 2) > W // 4
        np.testing.assert_allclose(middle[mask], old[rows // 2, :, :3][mask],
                                   atol=2e-4)

    def test_zero_visibility_returns_black(self):
        image = self.image(self.new_far, 0.0)
        self.assertEqual(float(image[:, :, :3].max()), 0.0)

    def test_deterministic(self):
        a = self.image(self.new_far)
        b = self.image(self.new_far)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
