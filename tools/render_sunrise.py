"""Render sunrise sky, aerial depth and the actual water solar path on the GPU."""
import argparse
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import Renderer, look_at
from compare_performance import archive_source
from build import ROOT, shader_digest


class LakeRenderer(Renderer):
    def check(self,stage):
        super().check(stage)
        if stage=='water':
            self.water_hdr=self.read(self.w,self.h)[::-1,:,:3]

    def use(self,name,*args):
        self.active_pass=name
        return super().use(name,*args)

    def quad(self,p,vertices,normal,color,block=0,sky=1.0,torch=0.0):
        if self.active_pass=='gbuffers_water':
            vertices=[(-150,64,60),(150,64,60),(150,64,-350),(-150,64,-350)]
        return super().quad(p,vertices,normal,color,block,sky,torch)

    def scene(self,p,kind):
        self.box(p,(0,55,-110),(300,2,500),(0.35,0.38,0.30))
        self.box(p,(12,63,-64),(19,3,16),(0.33,0.38,0.23))
        for x in [6,18]:
            for z in [-59,-69]:
                self.box(p,(x,68,z),(1.1,8,1.1),(0.51,0.30,0.16))
        self.box(p,(12,72,-64),(19,1,17),(0.25,0.28,0.25))
        self.box(p,(12,73,-64),(15,1,13),(0.26,0.29,0.25))
        self.box(p,(12,74,-64),(11,1,9),(0.28,0.31,0.27))
        self.box(p,(12,75,-64),(6,1,5),(0.30,0.33,0.28))
        # Distant silhouettes reveal the depth-dependent golden mist.
        for x,z,h in [(-43,-105,12),(-22,-133,18),(45,-160,14),(-9,-204,23)]:
            self.box(p,(x,63+h/2,z),(8,h,8),(0.44,0.43,0.38))
        self.box(p,(0,62,-255),(300,4,14),(0.31,0.37,0.24))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',default='Galaxy Shader-1.13.1.zip')
    args=parser.parse_args()
    with zipfile.ZipFile(ROOT/args.baseline) as archive:
        before=archive_source(archive)
    after=render_smoke.source_for
    r=LakeRenderer(960,540)
    r.camera=np.array([0,66,12],dtype=np.float32)
    r.translation[:3,3]=-r.camera
    r.rotation=look_at(np.zeros(3),np.array([0.0,-0.04,-1.0]))
    caches={'before':{},'after':{}}
    report={'type':'Synthetic lake; not Minecraft gameplay',
            'shader_sha256':shader_digest(),'baseline':args.baseline,
            'options':{'CLOUD_QUALITY':0},'scenarios':{}}
    rows=[]
    try:
        for label,sun in [('sunrise',[0.0,0.055,-1.0]),
                          ('early-morning',[0.0,0.18,-1.0]),
                          ('noon',[0.4,0.8,-0.4])]:
            frames={}
            for variant,source in [('before',before),('after',after)]:
                render_smoke.source_for=source
                r.programs=caches[variant]
                for frame in range(20):
                    im,metrics=r.render('day',options=report['options'],time=frame/30.0,
                                        sun_direction=sun,preserve_history=frame>0)
                frames[variant]=im
                im.save(ROOT/f'validation/sunrise-{label}-{variant}.png')
                report['scenarios'][label+'-'+variant]=metrics
            rows.append((label,frames))
            print(label+' rendered',flush=True)
        # Inspect the real water pass in HDR, before fog/bloom can add a glow.
        # Opposite sun azimuths must move the reflection path correspondingly.
        render_smoke.source_for=after
        r.programs=caches['after']
        centroids=[]
        for sx in [-0.14,0.14]:
            for frame in range(8):
                r.render('day',options=report['options'],time=0.6,
                         sun_direction=[sx,0.055,-1.0],preserve_history=frame>0)
            region=r.water_hdr[int(r.h*0.55):]
            lum=region@np.array([0.2126,0.7152,0.0722])
            weight=np.maximum(lum-1.0,0.0)
            assert weight.sum()>1.0,'Water must contain a resolved HDR solar path'
            centroids.append(float((weight*np.arange(r.w)[None,:]).sum()/weight.sum()))
        assert centroids[1]>centroids[0]+40.0,('Solar path must follow the sun',centroids)
        report['checks']={'hdr_solar_path_moves_with_sun':True,
                          'water_glint_x_centroids':centroids}
    finally:
        render_smoke.source_for=after
        r.programs={('variant',v,*key):p for v,cache in caches.items() for key,p in cache.items()}
        r.close()
    sheet=Image.new('RGB',(1920,574*len(rows)),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for row,(label,frames) in enumerate(rows):
        for col,v in enumerate(['before','after']):
            x=col*960;y=row*574
            sheet.paste(frames[v],(x,y+34))
            draw.text((x+12,y+10),'SYNTHETIC LAKE / CLOUDS OFF / '+label.upper()+' / '+v.upper(),
                      fill=(230,232,235))
    sheet.save(ROOT/'validation/sunrise-comparison.png')
    report['status']='passed; appearance reviewed in paired synthetic views'
    (ROOT/'validation/sunrise-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
