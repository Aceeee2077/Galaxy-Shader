"""GPU checks for the large hanging pleats in the auroral curtain.

The fixture samples auroraSky() with AURORA_FOLDS compiled on and off. It
measures curtain displacement and brightness gathering, not final exposure.
"""
import re
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


W, H = 320, 160
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
OFF, ON = 0, 1
BAND = np.s_[24:82, :]
NORTH_COLUMNS = np.s_[30:290]


def fragment(folds):
    common = expand(SHADERS / 'lib/common.glsl')
    common = re.sub(r'^\s*#define\s+AURORA_FOLDS\s+\S+',
                    f'#define AURORA_FOLDS {folds}', common, flags=re.M)
    return ('#version 330 compatibility\n' + common +
            expand(SHADERS / 'lib/night_sky.glsl') +
            '''
uniform vec2 testResolution;
uniform float testNight;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.60;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    gl_FragColor = vec4(auroraSky(ray, testNight), 1.0);
}''')


class AuroraFoldsRegression(unittest.TestCase):
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
            cls.renderer.uniform(program, 'testNight', 1.0)

    @classmethod
    def tearDownClass(cls):
        for program in cls.programs.values():
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, state, night=1.0, time=70.0):
        program = cls.programs[state]
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'testNight', night)
        cls.renderer.uniform(program, 'frameTimeCounter', time)
        cls.renderer.full_screen()
        cls.renderer.check('aurora folds')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    @staticmethod
    def column_shifts(off, on):
        shifts = []
        for x in range(20, W - 20):
            a = off[0:110, x, 1]
            b = on[0:110, x, 1]
            if a.max() < 1e-5 or b.max() < 1e-5:
                continue
            a = (a - a.mean()) / max(a.std(), 1e-6)
            b = (b - b.mean()) / max(b.std(), 1e-6)
            scores = [float(np.dot(a, np.roll(b, s))) for s in range(-22, 23)]
            shifts.append(float(np.argmax(scores) - 22))
        return np.array(shifts)

    def test_deterministic(self):
        a = self.image(ON, time=321.0)
        b = self.image(ON, time=321.0)
        np.testing.assert_array_equal(a, b, 'Folds must be frame-stable')

    def test_folds_displace_the_curtain(self):
        shifts = self.column_shifts(self.image(OFF), self.image(ON))
        self.assertGreater(len(shifts), 120)
        self.assertGreater(float(np.abs(shifts).mean()), 1.0,
                           'Hanging pleats must move the curtain vertically')
        self.assertGreater(float(shifts.std()), 2.0,
                           'Pleat depth must vary across the curtain')

    def test_pleats_gather_the_rays(self):
        off = self.image(OFF)[:, :, 1]
        on = self.image(ON)[:, :, 1]
        mask = off > 1e-5
        ratio = np.ones_like(off)
        ratio[mask] = on[mask] / off[mask]
        active = ratio[mask]
        self.assertGreater(float(active.std()), float(active.mean()) * 0.12,
                           'Folds must bunch the curtain instead of tinting it')
        self.assertGreater(float(active.max() - active.min()), 0.20,
                           'Crests and troughs must separate in brightness')

    def test_north_and_night_gates(self):
        image = self.image(ON)
        south = image[:, 240:280]
        self.assertLess(float(south.max()), 1e-7,
                        'Southern sky must stay free of aurora')
        self.assertLess(float(self.image(ON, night=0.0).max()), 1e-7)

    def test_colour_stays_auroral(self):
        image = self.image(ON)
        active = image[image[:, :, 1] > 0.001]
        red, green, blue = (float(active[:, c].mean()) for c in range(3))
        self.assertGreater(green, red * 2.2, 'Aurora must stay green')
        self.assertGreater(blue, red * 1.5, 'Cool violet/teal must stay present')


if __name__ == '__main__':
    unittest.main()
