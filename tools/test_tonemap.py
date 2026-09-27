"""Exercise the shipped tone curve on the GPU, including dark-sky regression."""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


class ToneMapRegression(unittest.TestCase):
    def test_black_shadow_and_highlight_response(self):
        renderer=Renderer(8,8)
        vertex='#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fragment=('#version 330 compatibility\n'+expand(SHADERS/'lib/common.glsl')+
                  expand(SHADERS/'lib/tonemap.glsl')+
                  '\nuniform vec3 inputColor;\nvoid main(){gl_FragColor=vec4(naturalFilmic(inputColor),1.0);}')
        program=renderer.gl.compile(vertex,fragment)
        try:
            renderer.bind_fbo([renderer.final])
            renderer.call('glUseProgram',None,[U],program)
            levels=[]
            for value in [0.0,0.001,0.01,0.05,0.18,1.0,4.0,16.0,128.0]:
                renderer.uniform(program,'inputColor',[value]*3)
                renderer.full_screen()
                pixel=renderer.read(8,8)[0,0,:3]
                self.assertTrue(np.isfinite(pixel).all())
                self.assertGreaterEqual(float(pixel.min()),0.0)
                self.assertLessEqual(float(pixel.max()),1.0)
                levels.append(float(pixel.mean()))
            self.assertEqual(levels[0],0.0)
            self.assertLess(levels[2],0.01, 'Dark sky must not become a grey veil')
            self.assertTrue(np.all(np.diff(levels)>0.0), 'Exposure ramp must retain ordering')
            self.assertGreater(levels[-1],0.98)
            renderer.uniform(program,'inputColor',[20.0,8.0,1.0])
            renderer.full_screen()
            pixel=renderer.read(8,8)[0,0,:3]
            self.assertTrue(pixel[0]>=pixel[1]>=pixel[2])
            renderer.check('tone curve regression')
        finally:
            renderer.gl.delete_program(program)
            renderer.close()


if __name__=='__main__':unittest.main()
