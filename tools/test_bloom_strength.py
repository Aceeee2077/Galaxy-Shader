"""GPU checks for the zero-strength bloom early-out.

The bright pass is sixteen taps and each blur pass is five. At strength zero
the result is multiplied away in composite4, so all three passes now skip that
work. Each pass must output exactly zero at strength 0 even with an HDR input,
and must still produce a non-zero bloom at strength 1.
"""
import unittest
import numpy as np
from build import SHADERS
from validate import source_for
from render_smoke import Renderer, U

W = H = 64
VERTEX = ('#version 330 compatibility\n' +
          (SHADERS / 'program' / 'fullscreen.vsh').read_text())


class BloomStrengthRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(W, H)
        cls.programs = {}
        for name in ('composite1', 'composite2', 'composite3'):
            for strength in ('0.0', '1.0'):
                source = source_for(SHADERS / 'program' / f'{name}.fsh',
                                    {'BLOOM_STRENGTH': strength})
                cls.programs[(name, strength)] = cls.renderer.gl.compile(
                    VERTEX, source)
        cls.bright = cls.renderer.texture(
            4, 4, data=np.full((4, 4, 4), 4.0, np.float32))

    @classmethod
    def tearDownClass(cls):
        for program in cls.programs.values():
            cls.renderer.gl.delete_program(program)
        cls.renderer.close()

    @classmethod
    def image(cls, name, strength, sampler):
        program = cls.programs[(name, strength)]
        cls.renderer.bind_fbo([cls.renderer.final])
        cls.renderer.call('glUseProgram', None, [U], program)
        cls.renderer.uniform(program, 'viewWidth', float(W))
        cls.renderer.uniform(program, 'viewHeight', float(H))
        cls.renderer.uniform(program, 'frameTimeCounter', 0.0)
        cls.renderer.call('glActiveTexture', None, [U], 0x84C0)
        cls.renderer.call('glBindTexture', None, [U, U], 0x0DE1, cls.bright)
        cls.renderer.uniform(program, sampler, 0)
        cls.renderer.full_screen()
        cls.renderer.check(f'{name} bloom strength')
        data = cls.renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    def test_zero_strength_writes_zero(self):
        for name, sampler in (('composite1', 'colortex0'),
                              ('composite2', 'colortex5'),
                              ('composite3', 'colortex6')):
            data = self.image(name, '0.0', sampler)
            self.assertEqual(float(np.abs(data).max()), 0.0,
                             f'{name} must skip all bloom taps at strength 0')

    def test_enabled_strength_still_blooms(self):
        for name, sampler in (('composite1', 'colortex0'),
                              ('composite2', 'colortex5'),
                              ('composite3', 'colortex6')):
            data = self.image(name, '1.0', sampler)
            self.assertGreater(float(data.max()), 0.0,
                               f'{name} must keep bloom at strength 1')

    def test_deterministic(self):
        np.testing.assert_array_equal(
            self.image('composite2', '1.0', 'colortex5'),
            self.image('composite2', '1.0', 'colortex5'))


if __name__ == '__main__':
    unittest.main()
