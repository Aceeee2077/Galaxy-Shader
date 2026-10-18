"""Compare this calibration to the saved working source, never to Photon renders."""
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import look_at
from render_sunlight import WoodlandRenderer
from render_sunrise import LakeRenderer
from compare_performance import archive_source
from build import ROOT, shader_digest


def main():
    baseline='tools/.cache/photon13-calibration-before.zip'
    with zipfile.ZipFile(ROOT/baseline) as archive:
        before=archive_source(archive)
    after=render_smoke.source_for
    report={'type':'Synthetic GPU fixtures; not Minecraft screenshots or Photon renders',
            'baseline':baseline,'shader_sha256':shader_digest(),'scenarios':{}}
    rows=[]
    for fixture in ['woodland','lake']:
        renderer=(WoodlandRenderer if fixture=='woodland' else LakeRenderer)(960,540)
        renderer.camera=np.array([3,65.3,15] if fixture=='woodland' else [0,66,12],np.float32)
        renderer.translation[:3,3]=-renderer.camera
        renderer.rotation=look_at(np.zeros(3),np.array([-0.08,0.045,-1.0] if fixture=='woodland' else [0,-0.04,-1]))
        caches={'before':{},'after':{}}
        cases=([('morning','day',[-0.12,0.18,-1.0]),
                ('noon','day',[-0.4,0.75,-0.5]),
                ('rain','rain',[-0.12,0.18,-1.0])] if fixture=='woodland' else
               [('sunrise','day',[0,0.055,-1]),('blue-hour','day',[0,-0.08,-1]),
                ('noon','day',[0.4,0.8,-0.4])])
        try:
            for name,kind,sun in cases:
                label=fixture+'-'+name
                frames={}
                for variant,source in [('before',before),('after',after)]:
                    render_smoke.source_for=source
                    renderer.programs=caches[variant]
                    for frame in range(20):
                        im,metrics=renderer.render(kind,time=frame/30.0,sun_direction=sun,
                            options={'CLOUD_QUALITY':0} if fixture=='lake' else {'CLOUD_COVERAGE':0.35},
                            preserve_history=frame>0)
                    im.save(ROOT/f'validation/photon-{label}-{variant}.png')
                    frames[variant]=im
                    report['scenarios'][label+'-'+variant]=metrics
                delta=np.abs(np.asarray(frames['before'],float)-np.asarray(frames['after'],float))
                report['scenarios'][label+'-difference']={'mean_abs_8bit':float(delta.mean())}
                rows.append((label,frames))
                print(label+' rendered',flush=True)
        finally:
            render_smoke.source_for=after
            renderer.programs={('variant',v,*key):p for v,cache in caches.items() for key,p in cache.items()}
            renderer.close()
    sheet=Image.new('RGB',(1280,392*len(rows)),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for row,(label,frames) in enumerate(rows):
        for col,variant in enumerate(['before','after']):
            sheet.paste(frames[variant].resize((640,360)),(col*640,row*392+32))
            draw.text((col*640+12,row*392+10),'SYNTHETIC / '+label.upper()+' / '+variant.upper(),fill=(235,235,235))
    sheet.save(ROOT/'validation/photon-calibration-comparison.png')
    report['status']='rendered for visual review'
    (ROOT/'validation/photon-calibration-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
