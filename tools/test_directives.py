"""Regression for the Iris loading error reported in the user's game log."""
import unittest
from validate import validate_clear_colors
from build import SHADERS

class ClearColorRegression(unittest.TestCase):
    def test_glsl_scalar_splat_is_not_an_iris_directive(self):
        for index in [0,2,3]:
            with self.subTest(index=index), self.assertRaisesRegex(AssertionError,'four components'):
                validate_clear_colors(f'const vec4 colortex{index}ClearColor = vec4(0.0);')

    def test_four_numeric_components_are_valid(self):
        validate_clear_colors('const vec4 colortex1ClearColor = vec4(0.5, 0.5, 1.0, 1.0);')

    def test_shipped_clear_colors(self):
        validate_clear_colors((SHADERS/'lib/buffers.glsl').read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
