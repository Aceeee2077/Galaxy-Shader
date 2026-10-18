"""Paired synthetic woodland views for sunny direct-light review, not gameplay."""
import argparse
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import Renderer, look_at
from compare_performance import archive_source
from build import ROOT, shader_digest


class WoodlandRenderer(Renderer):
    def use(self,name,*args):
        self.active_pass=name
        return super().use(name,*args)

    def quad(self,*args,**kwargs):
        # The inherited fixture's water quad is unrelated to this woodland.
        if self.active_pass!='gbuffers_water':
            return super().quad(*args,**kwargs)

    def scene(self,p,kind):
        self.box(p,(0,62,-15),(90,2,120),(0.34,0.46,0.23))
        self.box(p,(8,63.05,0),(4,0.1,48),(0.66,0.51,0.32))
        for x,z in [(-9,-18),(10,0),(-15,2),(-2,-31),(18,-23)]:
            self.box(p,(x,66,z),(1,6,1),(0.70,0.71,0.64))
            for h in [64.2,65.8,67.5]:
                self.box(p,(x, h, z+0.515),(0.65,0.18,0.04),(0.16,0.18,0.15))
            for ix,iz in [(-1,0),(0,-1),(0,0),(0,1),(1,0),(-1,-1),(1,1)]:
                y=69.0+float((ix+2*iz)%3)*0.45
                self.box(p,(x+ix*1.65,y,z+iz*1.65),(2.1,2.2,2.1),
                         (0.33+ix*0.015,0.47,0.19+iz*0.01),10002)
            self.box(p,(x,71,z),(2.5,1.4,2.3),(0.36,0.49,0.20),10002)
        self.box(p,(15,65,-10),(5,4,9),(0.80,0.79,0.72))
        self.box(p,(-6,63.6,-4),(2.4,1.2,2.2),(0.57,0.59,0.56))
        self.box(p,(-3,63.4,-6),(1.5,0.8,1.5),(0.60,0.61,0.57))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',default='Galaxy Shader-1.13.1.zip')
    args=parser.parse_args()
    with zipfile.ZipFile(ROOT/args.baseline) as archive:
        before=archive_source(archive)
    after=render_smoke.source_for
    renderer=WoodlandRenderer(960,540)
    renderer.camera=np.array([3,65.3,15],dtype=np.float32)
    renderer.translation[:3,3]=-renderer.camera
    renderer.rotation=look_at(np.zeros(3),np.array([-0.08,0.045,-1.0]))
    caches={'before':{},'after':{}}
    report={'type':'Synthetic woodland; not Minecraft gameplay',
            'baseline':args.baseline,'shader_sha256':shader_digest(),
            'options':{'CLOUD_COVERAGE':0.35},'scenarios':{}}
    rows=[]
    try:
        for label,kind,sun,overrides in [('low-sun','day',[-0.12,0.18,-1.0],{}),
                               ('clear-sun','day',[-0.12,0.18,-1.0],{'CLOUD_QUALITY':0}),
                               ('noon','day',[-0.4,0.75,-0.5],{}),
                               ('rain','rain',[-0.12,0.18,-1.0],{})]:
            frames={}
            for variant,source in [('before',before),('after',after)]:
                render_smoke.source_for=source
                renderer.programs=caches[variant]
                for frame in range(20):
                    im,metrics=renderer.render(kind,time=frame/30.0,
                        options={**report['options'],**overrides},sun_direction=sun,preserve_history=frame>0)
                frames[variant]=im
                im.save(ROOT/f'validation/sunlight-{label}-{variant}.png')
                report['scenarios'][label+'-'+variant]=metrics
                metrics['options']={**report['options'],**overrides}
            rows.append((label,frames))
            print(label+' rendered',flush=True)
    finally:
        render_smoke.source_for=after
        renderer.programs={('variant',variant,*key):p
            for variant,cache in caches.items() for key,p in cache.items()}
        renderer.close()
    sheet=Image.new('RGB',(1920,574*len(rows)),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for row,(label,frames) in enumerate(rows):
        for col,variant in enumerate(['before','after']):
            x=col*960; y=row*574
            sheet.paste(frames[variant],(x,y+34))
            draw.text((x+12,y+10),'SYNTHETIC WOODLAND / '+label.upper()+' / '+variant.upper(),
                      fill=(230,232,235))
    sheet.save(ROOT/'validation/sunlight-comparison.png')
    report['status']='rendered for visual review'
    (ROOT/'validation/sunlight-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
