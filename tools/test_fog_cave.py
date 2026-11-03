"""GPU checks for the enclosed-space fog early-out.

Terrain fog samples the sky to colour aerial haze. In a cave or an interior the
outdoor weight is exactly zero, so the sample can never reach the result. These
tests compare the gated code against the previous unconditional version in
caves, indoors and outdoors.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W = H = 64
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATED = '        if (!sky && outdoor > 0.0) clearScatter=atmosphere(ray,false);'
UNGATED = '        clearScatter=atmosphere(ray,false);'


def fog_source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/fog.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testPlayer;
uniform float testColor;
uniform int testSky;
void main() {
    vec3 color = applyFog(vec3(testColor), testPlayer, testSky != 0);
    gl_FragColor = vec4(color, 1.0);
}''')


class FogCaveRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        source = fog_source()
        assert GATED in source
        cls.new = cls.renderer.gl.compile(VERTEX, source)
        cls.old = cls.renderer.gl.compile(VERTEX, source.replace(GATED, UNGATED))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.old):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, player, sky_light, sky=0, rain=0.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'testPlayer', list(player))
        cls.renderer.uniform(program, 'testColor', 0.5)
        cls.renderer.uniform(program, 'testSky', sky)
        cls.renderer.uniform(program, 'eyeBrightnessSmooth', [0, sky_light])
        cls.renderer.uniform(program, 'sunPosition', [80.0, 2.0, 60.0])
        cls.renderer.uniform(program, 'moonPosition', [-80.0, -2.0, -60.0])
        cls.renderer.uniform(program, 'cameraPosition', [0.0, 70.0, 0.0])
        cls.renderer.uniform(program, 'rainStrength', rain)
        cls.renderer.uniform(program, 'isEyeInWater', 0)
        cls.renderer.uniform(program, 'far', 1024.0)
        cls.renderer.full_screen()
        cls.renderer.check('fog cave')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_cave_matches_previous_code(self):
        player = (140.0, 5.0, -90.0)
        a = self.image(self.new, player, 0)
        b = self.image(self.old, player, 0)
        np.testing.assert_allclose(a, b, atol=2e-4,
                                   err_msg='A cave fog result must be unchanged')

    def test_cave_ignores_the_ray(self):
        # Mirrored rays: same length, same heights, so the only difference is
        # the sky direction the atmosphere sample would have seen.
        left = self.image(self.new, (170.0, 170.0, 0.0), 0)
        right = self.image(self.new, (-170.0, 170.0, 0.0), 0)
        np.testing.assert_allclose(left, right, atol=2e-4,
                                   err_msg='Cave fog must not depend on the sky ray')

    def test_outdoor_keeps_the_sky_sample(self):
        for sky_light in (240, 60):
            a = self.image(self.new, (140.0, 5.0, -90.0), sky_light)
            b = self.image(self.old, (140.0, 5.0, -90.0), sky_light)
            np.testing.assert_allclose(
                a, b, atol=2e-4,
                err_msg=f'Outdoor fog changed at sky light {sky_light}')

    def test_outdoor_depends_on_the_ray(self):
        left = self.image(self.new, (170.0, 170.0, 0.0), 240)
        right = self.image(self.new, (-170.0, 170.0, 0.0), 240)
        self.assertGreater(float(np.abs(left - right).max()), 1e-4,
                           'Outdoor fog must still read the sky')

    def test_sky_flag_matches_previous_code(self):
        a = self.image(self.new, (140.0, 5.0, -90.0), 240, sky=1, rain=0.4)
        b = self.image(self.old, (140.0, 5.0, -90.0), 240, sky=1, rain=0.4)
        np.testing.assert_allclose(a, b, atol=2e-4)

    def test_deterministic(self):
        a = self.image(self.new, (140.0, 5.0, -90.0), 0)
        b = self.image(self.new, (140.0, 5.0, -90.0), 0)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
