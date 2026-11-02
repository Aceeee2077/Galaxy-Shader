"""GPU checks for the crossed gravity-wave trains in the noctilucent sheet.

The fixture samples noctilucentClouds() with the NLC_WAVES option compiled on
and off, then measures the on/off ratio. That ratio isolates the wave
modulation from cloud coverage and atmospheric gates.
"""
import re
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 240, 140
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
OFF, ON = 0, 1
LOW = np.s_[12:64, 20:220]


def fragment(waves):
    common = expand(SHADERS / 'lib/common.glsl')
    common = re.sub(r'^\s*#define\s+NLC_WAVES\s+\S+',
                    f'#define NLC_WAVES {waves}', common, flags=re.M)
    return ('#version 330 compatibility\n' + common +
            expand(SHADERS / 'lib/noctilucent.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testSummer;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.70;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(noctilucentClouds(ray, normalize(testSun),
                                          testOvercast, testSummer), 1.0);
}''')


class NlcWavesRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.programs = {}
        for state in (OFF, ON):
            cls.programs[state] = cls.renderer.gl.compile(VERTEX,
                                                          fragment(state))
        cls.renderer.bind_fbo([cls.renderer.final])
        for program in cls.programs.values():
            cls.renderer.call('glUseProgram', None, [U], program)
            cls.renderer.uniform(program, 'gbufferModelViewInverse',
                                 np.eye(4, dtype=np.float32))
            cls.renderer.uniform(program, 'testResolution', [W, H])
            cls.renderer.uniform(program, 'testSummer', 1.0)
            cls.renderer.uniform(program, 'testOvercast', 0.0)
            cls.renderer.uniform(program, 'testSun', [0.984, -0.18, 0.0])

    @classmethod
    def tearDownClass(cls):
        for program in cls.programs.values():
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, state, sun_height=-0.18, summer=1.0, overcast=0.0,
              time=80.0):
        program = cls.programs[state]
        cls.renderer.call('glUseProgram', None, [U], program)
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        cls.renderer.uniform(program, 'testSun',
                             [horizontal, sun_height, 0.0])
        cls.renderer.uniform(program, 'testSummer', summer)
        cls.renderer.uniform(program, 'testOvercast', overcast)
        cls.renderer.uniform(program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('noctilucent waves')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def wave_ratio(self, time=80.0):
        off = self.image(OFF, time=time)[:, :, 2]
        on = self.image(ON, time=time)[:, :, 2]
        mask = off > 1e-6
        ratio = np.ones_like(off)
        ratio[mask] = on[mask] / off[mask]
        return ratio, mask

    def test_deterministic(self):
        a = self.image(ON, time=321.0)
        b = self.image(ON, time=321.0)
        np.testing.assert_array_equal(a, b, 'Wave trains must be stable')

    def test_waves_add_fine_structure(self):
        ratio, mask = self.wave_ratio()
        self.assertGreater(int(mask.sum()), 2000,
                           'Fixture must contain enough cloud pixels')
        active = ratio[mask]
        self.assertGreater(float(active.std()), float(active.mean()) * 0.12,
                           'Crossed waves must break up the smooth veil')
        self.assertGreater(float(active.max() - active.min()), 0.25,
                           'Crests and troughs must be visually separated')

    def test_trains_cross_both_axes(self):
        ratio, mask = self.wave_ratio()
        region = ratio[LOW]
        valid = mask[LOW]
        rows = np.array([region[i][valid[i]].mean()
                         for i in range(region.shape[0]) if valid[i].any()])
        columns = np.array([region[:, j][valid[:, j]].mean()
                            for j in range(region.shape[1])
                            if valid[:, j].any()])
        self.assertGreater(float(rows.std()), 0.015,
                           'Wave phase must vary with elevation')
        self.assertGreater(float(columns.std()), 0.015,
                           'Wave phase must vary across azimuth')

    def test_gates_still_hold(self):
        self.assertLess(float(self.image(ON, sun_height=0.20).max()), 1e-7)
        self.assertLess(float(self.image(ON, sun_height=-0.75).max()), 1e-7)
        self.assertLess(float(self.image(ON, overcast=1.0).max()), 1e-7)
        self.assertGreater(float(self.image(ON).max()), 0.004)

    def test_drift_is_slow_but_visible(self):
        first, mask = self.wave_ratio(time=80.0)
        later, _ = self.wave_ratio(time=500.0)
        difference = np.abs(first - later)[mask]
        self.assertGreater(float(difference.mean()), 1e-3,
                           'Crests must drift over several minutes')
        self.assertLess(float(difference.mean()), 0.35,
                        'Drift must stay far slower than cloud weather')


if __name__ == '__main__':
    unittest.main()
