"""Exercise the shipped tone curve on the GPU, including dark-sky regression."""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


class ToneMapRegression(unittest.TestCase):
    def test_warm_grade_keeps_black_color_identity_and_highlight_detail(self):
        renderer=Renderer(8,8)
        vertex='#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fragment=('#version 330 compatibility\n#define DIMENSION 0\n'+
                  expand(SHADERS/'lib/common.glsl')+expand(SHADERS/'lib/tonemap.glsl')+
                  '\nuniform vec3 inputColor;\nvoid main(){gl_FragColor=vec4(gradeColor(inputColor),1.0);}')
        program=renderer.gl.compile(vertex,fragment)
        try:
            renderer.bind_fbo([renderer.final])
            renderer.call('glUseProgram',None,[U],program)
            renderer.uniform(program,'gbufferModelViewInverse',np.eye(4,dtype=np.float32))
            renderer.uniform(program,'sunPosition',[0.0,1.0,0.0])

            def sample(color):
                renderer.uniform(program,'inputColor',color)
                renderer.full_screen()
                pixel=renderer.read(8,8)[0,0,:3]
                self.assertTrue(np.isfinite(pixel).all())
                self.assertGreaterEqual(float(pixel.min()),0.0)
                self.assertLessEqual(float(pixel.max()),1.0)
                return pixel

            np.testing.assert_array_equal(sample([0.0]*3),np.zeros(3))
            ramp=[sample([value]*3) for value in [0.01,0.05,0.18,1.0,4.0,16.0]]
            self.assertTrue(np.all(np.diff(np.array(ramp),axis=0)>0.0))
            self.assertGreater(float(ramp[2].mean()),0.53,'Midtones must stay bright')
            self.assertGreater(float(ramp[2][0]),float(ramp[2][2]),'Daylight grade must be warm')
            self.assertLess(float(ramp[-1].max()-ramp[-1].min()),0.03,
                            'Bright neutral highlights must approach white')
            foliage=sample([0.10,0.25,0.055])
            sky=sample([0.08,0.18,0.40])
            self.assertGreater(float(foliage[1]),float(foliage[0]))
            self.assertGreater(float(sky[2]),float(sky[1]))
            renderer.check('warm grade and highlight detail')
        finally:
            renderer.gl.delete_program(program)
            renderer.close()

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
