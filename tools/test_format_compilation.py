"""Use the real GPU to prove the old failure and the unmodified-source fix."""
import re
import unittest
from build import SHADERS
from validate import expand, source_for
from gl_context import GLContext

class FormatCompilationRegression(unittest.TestCase):
    def test_old_format_declarations_fail_and_commented_metadata_compiles(self):
        gl=GLContext()
        try:
            vertex=expand(SHADERS/'deferred.vsh')
            fixed=expand(SHADERS/'deferred.fsh')
            block=re.search(r'/\*\s*\n(const int colortex0Format.*?const int colortex6Format[^;]*;)\s*\n\*/',fixed,re.S)
            self.assertIsNotNone(block)
            old=fixed[:block.start()]+block[1]+fixed[block.end():]
            with self.assertRaisesRegex(RuntimeError, 'RGBA16F'):
                gl.compile(vertex,old)
            program=gl.compile(vertex,fixed)
            gl.delete_program(program)
            # The validation helper can add loader macros, never format symbols.
            patched=source_for(SHADERS/'deferred.fsh')
            self.assertEqual(patched.replace('#define IS_IRIS\n','',1),fixed)
        finally: gl.close()

if __name__=='__main__':unittest.main()
