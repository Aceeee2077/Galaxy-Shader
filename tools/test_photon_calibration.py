"""GPU checks of daylight color, finite sun size, exposure and low mist."""
import math
import unittest
import numpy as np
from build import SHADERS
from validate import expand
from render_smoke import Renderer, U


class PhotonCalibrationRegression(unittest.TestCase):
    def test_solar_disk_color_exposure_and_mist(self):
        r=Renderer(8,8)
        vertex='#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fragment=('#version 330 compatibility\n#define DIMENSION 0\n'+
            expand(SHADERS/'lib/common.glsl')+expand(SHADERS/'lib/atmosphere.glsl')+
            expand(SHADERS/'lib/tonemap.glsl')+expand(SHADERS/'lib/fog.glsl')+'''
uniform int testMode;
uniform vec3 testRay;
void main() {
    vec3 c=sunlightColor();
    if(testMode==1) c=atmosphere(testRay,true)-atmosphere(testRay,false);
    if(testMode==2) c=vec3(adaptedExposure());
    if(testMode==3) c=applyFog(vec3(0.1),vec3(0.0,0.0,-80.0),false);
    if(testMode==4) c=atmosphere(testRay,true);
    gl_FragColor=vec4(c,1.0);
}''').replace('#define COSMIC_SKY_QUALITY 2','#define COSMIC_SKY_QUALITY 0')
        p=r.gl.compile(vertex,fragment)
        try:
            r.bind_fbo([r.final]); r.call('glUseProgram',None,[U],p)
            r.uniform(p,'gbufferModelViewInverse',np.eye(4,dtype=np.float32))
            r.uniform(p,'far',512.0)
            r.uniform(p,'eyeBrightnessSmooth',[0,240])

            def sample(**uniforms):
                for key,value in uniforms.items():r.uniform(p,key,value)
                r.full_screen()
                c=r.read(8,8)[0,0,:3]
                self.assertTrue(np.isfinite(c).all())
                return c

            noon=sample(sunPosition=[0,1,0])
            morning=sample(sunPosition=[0,0.18,-math.sqrt(1-0.18**2)])
            sunrise=sample(sunPosition=[0,0.055,-math.sqrt(1-0.055**2)])
            self.assertGreater(float(noon[2]/noon[0]),0.78,'Warm daylight must retain blue energy')
            self.assertLess(float(noon[2]/noon[0]),0.90,'Daylight must have a warm bias')
            self.assertGreater(float(noon[2]),float(morning[2]))
            self.assertGreater(float(morning[2]),float(sunrise[2]))
            self.assertGreater(float(sunrise[0]/sunrise[2]),4.0,'Low sun must warm naturally')
            self.assertGreater(float(sunrise[0]/sunrise[2]),
                               float(noon[0]/noon[2])*2.5,
                               'Warmth must grow with air mass')
            self.assertGreater(float(sunrise[1]/sunrise[2]),1.5,
                               'Ozone must keep the low sun orange, not magenta')

            # The reference radius is 2 degrees, independently of resolution.
            sun=np.array([0,0.2,-math.sqrt(1-0.2**2)])
            def ray_at(degrees):
                a=math.radians(degrees)
                return sun*math.cos(a)+np.array([1,0,0])*math.sin(a)
            inside=sample(testMode=1,sunPosition=sun,testRay=ray_at(1.5))
            outside=sample(testRay=ray_at(2.5))
            self.assertGreater(float(inside.mean()),8.0)
            self.assertLess(float(np.abs(outside).max()),0.001)
            # The aureole lives outside the occluded-disk difference, so sample
            # the full sky. Compare B/R to cancel the absolute intensity.
            inner_halo=sample(testMode=4,sunPosition=sun,testRay=ray_at(2.4))
            outer_halo=sample(testMode=4,sunPosition=sun,testRay=ray_at(4.0))
            inner_ratio=float(inner_halo[2]/inner_halo[0])
            outer_ratio=float(outer_halo[2]/outer_halo[0])
            self.assertGreater(outer_ratio,inner_ratio*1.3,
                               'Aureole must cool from the core outward')

            # Fixed exposure must not pump when moving from outdoors to caves.
            outdoor=sample(testMode=2,eyeBrightnessSmooth=[0,240])
            cave=sample(eyeBrightnessSmooth=[0,0])
            np.testing.assert_array_equal(outdoor,cave)
            self.assertAlmostEqual(float(outdoor[0]),1.25,places=3)

            low=sample(testMode=3,eyeBrightnessSmooth=[0,240],cameraPosition=[0,65,0],
                       sunPosition=[0,0.055,-1])
            high=sample(cameraPosition=[0,120,0])
            low_delta=float(np.linalg.norm(low-0.1))
            high_delta=float(np.linalg.norm(high-0.1))
            self.assertGreater(low_delta,high_delta*1.5,'Dawn mist must concentrate in lowlands')
            r.check('Photon parameter calibration')
        finally:
            r.gl.delete_program(p)
            r.close()


if __name__=='__main__':unittest.main()
