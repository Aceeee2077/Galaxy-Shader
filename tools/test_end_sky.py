"""GPU visual and temporal checks for the shipped End sky, not gameplay capture."""
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, shader_digest
from render_smoke import Renderer, look_at


def main():
    out=ROOT/'validation'
    renderer=Renderer(960,540)
    renderer.rotation=look_at(np.zeros(3),np.array([0.0,0.58,-1.0]))
    scale=1/math.tan(math.radians(82)/2)
    renderer.projection[0,0]=scale/(renderer.w/renderer.h)
    renderer.projection[1,1]=scale
    report={'type':'Synthetic GPU sky fixture; not Minecraft gameplay',
            'shader_sha256':shader_digest(), 'checks':{}}
    try:
        # Keep actual geometry for a foreground-occlusion regression. Disable
        # post filters that legitimately spread sky colors across silhouettes.
        opts={'BLOOM_QUALITY':0,'AA_QUALITY':0}
        on,_=renderer.render('end',options=opts,time=0.0)
        renderer.bind_fbo([renderer.buffers[3]])
        meta=renderer.read(renderer.w,renderer.h)[::-1]
        foreground=meta[:,:,3]>0.5
        off,_=renderer.render('end',options={**opts,'END_PLANETS':0},time=0.0)
        diff=np.abs(np.asarray(on,dtype=int)-np.asarray(off,dtype=int))
        assert foreground.any(), 'Occlusion fixture must include opaque terrain'
        assert diff[foreground].max()==0, 'Sky rendered over opaque terrain'
        report['checks']['opaque_terrain_unchanged']=True
        # Look above the horizon without synthetic terrain for the visual sheet.
        renderer.scene=lambda program,kind:None
        zero,_=renderer.render('end',time=0.0)
        zero.save(out/'end-planets-preview.png')
        later,_=renderer.render('end',time=60.0)
        assert np.mean(np.abs(np.asarray(zero,dtype=float)-np.asarray(later,dtype=float)))>1.0
        report['checks']['orbits_change_at_fixed_camera']=True
        frozen0,_=renderer.render('end',options={'END_ORBIT_SPEED':'0.0'},time=0.0)
        frozen1,_=renderer.render('end',options={'END_ORBIT_SPEED':'0.0'},time=173.0)
        assert np.array_equal(frozen0,frozen1), 'Frozen planets must remain stationary'
        report['checks']['zero_speed_freezes_sky']=True
        for speed in ['0.5','1.0','2.0']:
            start,_=renderer.render('end',options={'END_ORBIT_SPEED':speed},time=0.0)
            wrap,_=renderer.render('end',options={'END_ORBIT_SPEED':speed},time=3600.0)
            assert np.array_equal(start,wrap), f'Clock reset seam at speed {speed}'
        report['checks']['all_speeds_match_at_clock_reset']=True
        disabled0,_=renderer.render('end',options={'END_PLANETS':0},time=0.0)
        disabled1,_=renderer.render('end',options={'END_PLANETS':0},time=173.0)
        assert np.array_equal(disabled0,disabled1)
        report['checks']['disabled_sky_is_static']=True
        for dimension in ['day','nether']:
            a,_=renderer.render(dimension,options={'END_PLANETS':0})
            b,_=renderer.render(dimension,options={'END_PLANETS':1})
            assert np.array_equal(a,b), f'End effect leaked into {dimension}'
        report['checks']['other_dimensions_unchanged']=True
        frames=[]
        for i in range(25):
            frame,_=renderer.render('end',time=float(i*6))
            draw=ImageDraw.Draw(frame)
            draw.text((16,16),f'SYNTHETIC GPU PREVIEW / END SKY / {i*6:03d}s / 40x speed',fill=(180,195,220))
            frames.append(frame)
        frames[0].save(out/'end-planets-orbit.gif',save_all=True,append_images=frames[1:],
                       duration=150,loop=0,optimize=False)
        sheet=Image.new('RGB',(960,540*3))
        for row,index in enumerate([0,12,24]):sheet.paste(frames[index],(0,540*row))
        sheet.save(out/'end-planets-timeline.png')
        report['status']='passed'
    finally:
        renderer.close()
    (out/'end-sky-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
