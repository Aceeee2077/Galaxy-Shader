"""Warm palette A/B against a release ZIP using identical synthetic GPU scenes."""
import argparse
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import Renderer, look_at
from render_sunlight import WoodlandRenderer
from render_sunrise import LakeRenderer
from compare_performance import archive_source
from build import ROOT, shader_digest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',default='Galaxy Shader-1.14.0.zip')
    args=parser.parse_args()
    with zipfile.ZipFile(ROOT/args.baseline) as archive:
        before=archive_source(archive)
    current=render_smoke.source_for
    report={'type':'Synthetic GPU fixtures; not Minecraft screenshots',
            'baseline':args.baseline,'shader_sha256':shader_digest(),'scenarios':{}}
    rows=[]
    fixtures=[('woodland',WoodlandRenderer,[
        ('morning','day',[-0.12,0.18,-1.0]),
        ('noon','day',[-0.4,0.75,-0.5]),
        ('overcast','cloudy',[-0.4,0.75,-0.5]),
        ('rain','rain',[-0.12,0.18,-1.0])]),
        ('lake',LakeRenderer,[('sunrise','day',[0,0.055,-1]),
                              ('noon','day',[0.4,0.8,-0.4])]),
        ('interior',Renderer,[('night','night',None),('cave','cave',None)])]
    for fixture,renderer_type,cases in fixtures:
        renderer=renderer_type(960,540)
        if fixture!='interior':
            renderer.camera=np.array([3,65.3,15] if fixture=='woodland' else [0,66,12],np.float32)
            renderer.translation[:3,3]=-renderer.camera
            renderer.rotation=look_at(np.zeros(3),np.array(
                [-0.08,0.045,-1] if fixture=='woodland' else [0,-0.04,-1]))
        caches={'before':{},'after':{}}
        try:
            for label,kind,sun in cases:
                name=fixture+'-'+label
                frames={}
                for variant,source in [('before',before),('after',current)]:
                    render_smoke.source_for=source
                    renderer.programs=caches[variant]
                    for frame in range(20):
                        im,metrics=renderer.render(kind,time=frame/30.0,sun_direction=sun,
                            options={'CLOUD_COVERAGE':0.35},preserve_history=frame>0)
                    frames[variant]=im
                    im.save(ROOT/f'validation/warm-{name}-{variant}.png')
                    rgb=np.asarray(im,dtype=float)/255.0
                    # Terrain ROI excludes most sky for a useful brightness comparison.
                    roi=rgb[int(rgb.shape[0]*0.6):]
                    metrics['foreground_luminance']=float((roi@[0.2126,0.7152,0.0722]).mean())
                    metrics['foreground_red_blue_ratio']=float(roi[:,:,0].mean()/max(roi[:,:,2].mean(),1e-6))
                    report['scenarios'][name+'-'+variant]=metrics
                rows.append((name,frames))
                print(name+' rendered',flush=True)
        finally:
            render_smoke.source_for=current
            renderer.programs={('variant',v,*key):p for v,cache in caches.items() for key,p in cache.items()}
            renderer.close()
    sheet=Image.new('RGB',(1280,392*len(rows)),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for row,(name,frames) in enumerate(rows):
        for col,variant in enumerate(['before','after']):
            sheet.paste(frames[variant].resize((640,360)),(col*640,row*392+32))
            draw.text((col*640+12,row*392+10),'SYNTHETIC / '+name.upper()+' / '+variant.upper(),fill=(235,235,235))
    sheet.save(ROOT/'validation/warm-palette-comparison.png')
    sheet.crop((0,0,1280,392*3)).save(ROOT/'Galaxy Shader/previews/warm-palette.png')
    report['status']='rendered for visual review'
    (ROOT/'validation/warm-palette-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
