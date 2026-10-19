"""GPU checks for sky-fill directionality and occluded leaf transmission."""
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


class SkyLightingRegression(unittest.TestCase):
    def test_sky_fill_and_thin_foliage(self):
        renderer=Renderer(8,8)
        vertex='#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fragment=('#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'+
                  expand(SHADERS/'lib/common.glsl')+expand(SHADERS/'lib/lighting.glsl')+
                  '''
uniform vec3 testNormal;
uniform int testMode;
uniform float testId, testSky;
void main() {
    vec3 c=skyIrradiance(testNormal);
    if(testMode==1) {
        Material m=defaultMaterial(vec3(0.18,0.35,0.10),testNormal);
        c=shadeSurface(m,vec3(0.0,0.0,-10.0),vec2(0.0,testSky),testId);
    }
    gl_FragColor=vec4(c,1.0);
}''')
        program=renderer.gl.compile(vertex,fragment)
        try:
            renderer.bind_fbo([renderer.final])
            renderer.call('glUseProgram',None,[U],program)
            for name in ['gbufferModelView','gbufferModelViewInverse','shadowModelView','shadowProjection']:
                renderer.uniform(program,name,np.eye(4,dtype=np.float32))
            renderer.uniform(program,'sunPosition',[0.0,0.8,-0.6])
            renderer.uniform(program,'shadowLightPosition',[0.0,0.8,-0.6])
            renderer.uniform(program,'testNormal',[0.0,1.0,0.0])

            def sample(**uniforms):
                for name,value in uniforms.items():renderer.uniform(program,name,value)
                renderer.full_screen()
                c=renderer.read(8,8)[0,0,:3]
                self.assertTrue(np.isfinite(c).all())
                self.assertGreaterEqual(float(c.min()),0.0)
                return c

            up=sample(testMode=0)
            side=sample(testNormal=[1.0,0.0,0.0])
            down=sample(testNormal=[0.0,-1.0,0.0])
            self.assertGreater(float(up.mean()),float(side.mean()))
            self.assertGreater(float(side.mean()),float(down.mean()))
            self.assertGreater(float(down.min()),0.0,'Ground-facing surfaces retain bounce')
            self.assertGreater(float(side[0]),float(side[2]),'Outdoor side fill must be warm')
            self.assertLess(float(up[2]/up[0]),1.15,'Sky fill must not turn shade strongly blue')
            storm=sample(testNormal=[0.0,1.0,0.0],rainStrength=1.0,thunderStrength=1.0)
            self.assertLess(float(storm.mean()),float(up.mean()))
            night=sample(rainStrength=0.0,thunderStrength=0.0,sunPosition=[0.0,-0.8,0.6])
            self.assertLess(float(night.mean()),float(up.mean())*0.2)
            renderer.uniform(program,'sunPosition',[0.0,0.3,-1.0])
            renderer.uniform(program,'shadowLightPosition',[0.0,0.3,-1.0])
            solid=sample(testMode=1,testNormal=[0.0,0.0,1.0],testId=0.0,testSky=1.0)
            leaves=sample(testId=10002.0)
            self.assertGreater(float(leaves.mean()),float(solid.mean())*1.1,
                               'Backlit leaves transmit sunlight')
            closed_leaves=sample(testSky=0.0)
            closed_solid=sample(testId=0.0)
            np.testing.assert_array_equal(closed_leaves,closed_solid,
                                          'Leaf transmission must not light a closed cave')
            renderer.check('sky and leaf regression')
        finally:
            renderer.gl.delete_program(program)
            renderer.close()


if __name__=='__main__':unittest.main()
