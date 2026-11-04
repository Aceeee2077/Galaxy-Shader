"""GPU checks for the twilight point that stands in for Venus.

The fixture points `atmosphere` at the planet's analytic direction over a six
degree field, where its core covers a handful of pixels. It is an engineering
check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 180
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '        if (venusWindow > 0.0) {'
GATE_OFF = '        if (venusWindow > 1.0) {'
SKY = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 sun = normalize(sunPosition);
    float elongation = 0.34 + 0.26 * sin(float(worldDay) * 0.0215);
    vec3 venus = normalize(sun * cos(elongation) +
                           vec3(0.0,1.0,0.0) * sin(elongation));
    vec3 helper = vec3(0.0,1.0,0.0);
    vec3 right = normalize(cross(venus, helper));
    vec3 up = cross(right, venus);
    float az = radians((uv.x-0.5)*6.0);
    float el = radians((uv.y-0.5)*6.0);
    vec3 ray = normalize(venus + right*tan(az) + up*tan(el));
    gl_FragColor = vec4(atmosphere(ray,true),1.0);
}'''


def shader_source(venus=True):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert core.count(GATE_NEW) == 1
    if not venus:
        core = core.replace(GATE_NEW, GATE_OFF)
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + SKY


class EveningStar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.off = cls.renderer.gl.compile(VERTEX, shader_source(venus=False))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.off):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, elevation=-9.0, storm=0.0):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        angle = np.deg2rad(elevation)
        direction = [float(np.cos(angle)) * 300.0,
                     float(np.sin(angle)) * 300.0, 0.0]
        cls.renderer.uniform(program, 'sunPosition', direction)
        cls.renderer.uniform(program, 'shadowLightPosition', direction)
        cls.renderer.uniform(program, 'moonPosition', [-v for v in direction])
        cls.renderer.uniform(program, 'worldTime', 6000)
        cls.renderer.uniform(program, 'worldDay', 60)
        cls.renderer.uniform(program, 'rainStrength', storm)
        cls.renderer.uniform(program, 'wetness', 0.0)
        cls.renderer.uniform(program, 'thunderStrength', storm)
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('evening star')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_twilight_shows_the_point(self):
        new = self.image(self.new)[:, :, :3]
        off = self.image(self.off)[:, :, :3]
        self.assertGreater(float(new.max()), float(off.max()) + 0.5)
        luminance = new.sum(axis=2)
        peak = np.unravel_index(int(np.argmax(luminance)), luminance.shape)
        self.assertLess(abs(peak[0] - (H - 1) / 2.0), 6.0)
        self.assertLess(abs(peak[1] - (W - 1) / 2.0), 6.0)

    def test_daytime_gate_is_closed(self):
        new = self.image(self.new, 25.0)
        off = self.image(self.off, 25.0)
        np.testing.assert_array_equal(new, off)

    def test_deep_night_gate_is_closed(self):
        new = self.image(self.new, -40.0)
        off = self.image(self.off, -40.0)
        np.testing.assert_array_equal(new, off)

    def test_storm_dim_the_point(self):
        clear = float(self.image(self.new)[:, :, :3].max())
        storm = float(self.image(self.new, storm=1.0)[:, :, :3].max())
        self.assertLess(storm, clear * 0.6)

    def test_deterministic(self):
        a = self.image(self.new)
        b = self.image(self.new)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
