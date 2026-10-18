"""GPU regressions for sunny/shaded contrast and day/weather transitions."""
import unittest
import math
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


class SunlightRegression(unittest.TestCase):
    def test_direct_light_separates_sun_from_shade(self):
        r=Renderer(8,8)
        vertex='#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fragment=('#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'+
            expand(SHADERS/'lib/common.glsl')+expand(SHADERS/'lib/lighting.glsl')+
            expand(SHADERS/'lib/tonemap.glsl')+expand(SHADERS/'lib/volumetrics.glsl')+
            expand(SHADERS/'lib/fog.glsl')+'''
uniform float testSky;
uniform int testMode;
void main() {
    Material m=defaultMaterial(vec3(0.18),vec3(0.0,1.0,0.0));
    vec3 c=shadeSurface(m,vec3(0.0,0.0,-10.0),vec2(0.0,testSky),0.0);
    if(testMode==1) c=gradeColor(c);
    if(testMode==2) c=directionalRadiance();
    if(testMode==3) c=volumetricLight(vec3(0.0,0.0,-10.0),false);
    if(testMode==4) c=vec3(goldenHourAmount());
    if(testMode==5) c=applyFog(vec3(0.10),vec3(0.0,0.0,-80.0),false);
    gl_FragColor=vec4(c,1.0);
}''')
        fragment=fragment.replace('#define CLOUD_QUALITY 3','#define CLOUD_QUALITY 0')
        p=r.gl.compile(vertex,fragment)
        dark=r.texture(1,1,data=np.zeros((1,1,4),np.float32))
        try:
            r.bind_fbo([r.final]); r.call('glUseProgram',None,[U],p)
            for name in ['gbufferModelView','gbufferModelViewInverse','shadowModelView']:
                r.uniform(p,name,np.eye(4,dtype=np.float32))
            projection=np.diag([0.05,0.05,0.05,1.0]).astype(np.float32)
            r.uniform(p,'shadowProjection',projection)
            r.uniform(p,'shadowtex0',0)
            r.uniform(p,'eyeBrightnessSmooth',[0,240])
            r.uniform(p,'testSky',1.0)

            def sample(texture=None,**uniforms):
                r.call('glActiveTexture',None,[U],0x84C0)
                r.call('glBindTexture',None,[U,U],0x0DE1,r.white if texture is None else texture)
                for name,value in uniforms.items():r.uniform(p,name,value)
                r.full_screen()
                c=r.read(8,8)[0,0,:3]
                self.assertTrue(np.isfinite(c).all())
                self.assertGreaterEqual(float(c.min()),0.0)
                return c

            for height in [0.08,0.18,0.45,0.8]:
                direction=[0.0,height,-np.sqrt(1.0-height*height)]
                lit=sample(sunPosition=direction,shadowLightPosition=direction,testMode=0)
                shade=sample(dark)
                self.assertGreater(float(lit.mean()/shade.mean()),2.0,
                    f'Clear sun must separate from shade at elevation sine {height}')
                lit_display=sample(testMode=1)
                shade_display=sample(dark)
                self.assertGreater(float(lit_display.mean()/shade_display.mean()),1.3)
            clear=sample(testMode=2,rainStrength=0.0,thunderStrength=0.0)
            rain=sample(rainStrength=1.0)
            self.assertLess(float(rain.mean()),float(clear.mean())*0.4)
            # Crossing the horizon must fade continuously, without a day/night flash.
            for h in [-0.04,0.0,0.045,0.12]:
                a=sample(rainStrength=0.0,sunPosition=[0.0,h-0.0001,-1.0])
                b=sample(sunPosition=[0.0,h+0.0001,-1.0])
                self.assertLess(float(np.abs(a-b).max()),0.02)
            cave_lit=sample(testMode=0,testSky=0.0)
            cave_shadow=sample(dark)
            np.testing.assert_array_equal(cave_lit,cave_shadow)
            # A uniformly lit air column follows Beer-Lambert attenuation and
            # its visibility variance is zero: no occlusion-generated shafts.
            direction=[0.0,0.18,-math.sqrt(1.0-0.18**2)]
            sun=sample(testMode=2,sunPosition=direction,shadowLightPosition=direction)
            volume=sample(testMode=3)
            forward=-direction[2]
            phase=forward**4*0.85+forward**16*1.45+0.010
            expected=sun*phase*(1.0-math.exp(-10.0*0.00085))
            np.testing.assert_allclose(volume,expected,rtol=0.015,atol=0.0001,
                err_msg='Uniform sunlight must not acquire artificial shaft contrast')
            for height,expected in [(-0.15,0.0),(0.04,1.0),(0.25,0.0),(0.8,0.0)]:
                direction=[0.0,height,-math.sqrt(1.0-height*height)]
                golden=sample(testMode=4,sunPosition=direction)
                self.assertAlmostEqual(float(golden.mean()),expected,places=3)
            dawn=sample(testMode=5,sunPosition=[0.0,0.055,-1.0])
            self.assertGreater(float(dawn[0]),float(dawn[2])*1.5,
                               'Distant sunward dawn mist must be golden')
            r.check('sunny contrast and horizon transitions')
        finally:
            r.gl.delete_program(p)
            r.close()


if __name__=='__main__':unittest.main()
