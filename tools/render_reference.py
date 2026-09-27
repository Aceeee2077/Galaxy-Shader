"""Reproducible reference-oriented GPU views; these are NOT Minecraft captures."""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, shader_digest
from render_smoke import Renderer, look_at


def main():
    renderer=Renderer(960,540)
    out=ROOT/'validation'
    original_scene=renderer.scene
    report={'type':'Synthetic GPU reference views, not Minecraft gameplay',
            'shader_sha256':shader_digest(),'checks':{}}
    frames=[]
    def settled(kind,sun):
        # Preview the actual temporal resolve after a short stationary-camera
        # warmup, rather than presenting the deliberately dithered first frame.
        for frame in range(16):
            im,metrics=renderer.render(kind,time=frame/30.0,sun_direction=sun,
                                       preserve_history=frame>0)
        return im,metrics
    try:
        renderer.scene=lambda program,kind:None
        renderer.rotation=look_at(np.zeros(3),np.array([0.0,0.55,-1.0]))
        for label,kind,sun in [('cumulus','day',[0.6,0.6,-0.8]),
                               ('golden-clouds','sunset',[0.3,0.12,-1.0]),
                               ('rain-clouds','rain',[0.3,0.12,-1.0]),
                               ('cosmos','end',None)]:
            im,metrics=settled(kind,sun)
            im.save(out/f'reference-{label}.png')
            frames.append((label,im))
            report[label]=metrics
        on,_=renderer.render('day',time=0.0,sun_direction=[0.6,0.6,-0.8])
        off,_=renderer.render('day',time=0.0,sun_direction=[0.6,0.6,-0.8],options={'CLOUD_QUALITY':0})
        delta=np.abs(np.asarray(on,dtype=float)-np.asarray(off,dtype=float))
        report['checks']['cloud_mean_difference']=float(delta.mean())
        report['checks']['cloud_spatial_difference_std']=float(delta.std())
        assert delta.mean()>5 and delta.std()>5, 'Clouds must form visible structured masses'
        renderer.scene=original_scene
        renderer.rotation=look_at(np.zeros(3),np.array([-0.4,-0.09,-1.0]))
        for label,kind in [('golden-terrain','sunset'),('golden-rain','rain')]:
            im,metrics=settled(kind,[-0.4,0.12,-1.0])
            im.save(out/f'reference-{label}.png')
            frames.append((label,im))
            report[label]=metrics
    finally:renderer.close()
    sheet=Image.new('RGB',(1920,574*3),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(frames):
        x=i%2*960;y=i//2*574
        sheet.paste(im,(x,y+34))
        draw.text((x+16,y+10),'SYNTHETIC GPU / '+label.upper(),fill=(230,232,235))
    sheet.save(out/'reference-contact-sheet.png')
    report['status']='passed'
    (out/'reference-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
