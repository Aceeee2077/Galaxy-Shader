"""GPU checks for the phase-dependent earthshine on the unlit lunar side.

The fixture calls `moonSky` directly around the moon direction. It is an
engineering check, not a Minecraft screenshot.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 180
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
PHASE_NEW = 'float earthshine = 0.45 + 1.10 * (1.0 - litFraction);'
PHASE_OLD = 'float earthshine = 1.0;'
FILL_NEW = 'vec3(0.028, 0.037, 0.058) * (1.0 - lit) * earthshine *'
FILL_OLD = 'vec3(0.010, 0.014, 0.022) * (1.0 - lit) * (0.4 + 0.6 * limb);'

# moonPhase 0 is full, 2 is quarter, 3 is a thin crescent, 4 is new.
FULL = 0
QUARTER = 2
CRESCENT = 3
NEW = 4


def shader_source(phase='new', fill='new'):
    core = (expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/atmospheric_refraction.glsl') +
            expand(SHADERS / 'lib/moon.glsl'))
    assert PHASE_NEW in core and FILL_NEW in core
    if phase == 'old':
        core = core.replace(PHASE_NEW, PHASE_OLD)
    if fill == 'old':
        core = core.replace(FILL_NEW, FILL_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 moon = normalize(vec3(1.0, 0.0, 0.0));
    vec3 right = normalize(cross(moon, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, moon);
    float az = radians((uv.x - 0.5) * 9.0);
    float el = radians((uv.y - 0.5) * 9.0);
    vec3 ray = normalize(moon + right * tan(az) + up * tan(el));
    gl_FragColor = vec4(moonSky(ray, 1.0, 0.0), 1.0);
}''')


class MoonEarthshine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.new = cls.renderer.gl.compile(VERTEX, shader_source())
        cls.fixed_phase = cls.renderer.gl.compile(
            VERTEX, shader_source(phase='old'))
        cls.previous = cls.renderer.gl.compile(
            VERTEX, shader_source(phase='old', fill='old'))

    @classmethod
    def tearDownClass(cls):
        for program in (cls.new, cls.fixed_phase, cls.previous):
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, program, phase):
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'gbufferModelViewInverse',
                             np.eye(4, dtype=np.float32))
        cls.renderer.uniform(program, 'testResolution', [W, H])
        cls.renderer.uniform(program, 'sunPosition', [300.0, 0.0, 0.0])
        cls.renderer.uniform(program, 'moonPosition', [300.0, 0.0, 0.0])
        cls.renderer.uniform(program, 'moonPhase', int(phase))
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.full_screen()
        cls.renderer.check('moon earthshine')
        data = cls.renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    def test_quarter_phase_factor_is_one(self):
        # litFraction is exactly 0.5 at the quarter, so the phase factor is
        # one and the only change is the brighter fill itself -- not the
        # phase dependence.
        new = self.image(self.new, QUARTER)[:, :, :3]
        fixed = self.image(self.fixed_phase, QUARTER)[:, :, :3]
        np.testing.assert_allclose(new, fixed, atol=2e-4)

    def test_crescent_phase_factor_brightens(self):
        new = self.image(self.new, CRESCENT)[:, :, :3]
        fixed = self.image(self.fixed_phase, CRESCENT)[:, :, :3]
        self.assertGreater(float(new.mean()), float(fixed.mean()))

    def test_crescent_fill_is_brighter_than_previous(self):
        new = self.image(self.new, CRESCENT)[:, :, :3]
        old = self.image(self.previous, CRESCENT)[:, :, :3]
        self.assertGreater(float(new.mean()), float(old.mean()))

    def test_full_moon_stays_dark_sided(self):
        # Almost no night side is visible at full phase, so the fill barely
        # contributes and the disk keeps its previous brightness.
        new = self.image(self.new, FULL)[:, :, :3]
        old = self.image(self.previous, FULL)[:, :, :3]
        self.assertLess(abs(float(new.mean()) - float(old.mean())), 5e-4)

    def test_fill_never_competes_with_the_lit_limb(self):
        new = self.image(self.new, CRESCENT)[:, :, :3]
        old = self.image(self.previous, CRESCENT)[:, :, :3]
        self.assertLess(float(new.max()), float(old.max()) * 1.01)

    def test_phase_factor_strongest_at_new_moon(self):
        # Seen from the Moon the Earth is full at new phase, so the fill has
        # to grow as the lit fraction shrinks.
        deltas = {}
        for phase in (FULL, CRESCENT, NEW):
            new = float(self.image(self.new, phase)[:, :, :3].mean())
            fixed = float(self.image(self.fixed_phase, phase)[:, :, :3].mean())
            deltas[phase] = new - fixed
        self.assertGreater(deltas[NEW], deltas[CRESCENT])
        self.assertGreater(deltas[CRESCENT], deltas[FULL])

    def test_deterministic(self):
        a = self.image(self.new, CRESCENT)
        b = self.image(self.new, CRESCENT)
        np.testing.assert_array_equal(a, b)


if __name__ == '__main__':
    unittest.main()
