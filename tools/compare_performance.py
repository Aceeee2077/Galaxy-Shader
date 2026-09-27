"""A/B actual GLSL against a released ZIP. GPU draw time, NOT Minecraft FPS."""
import argparse
import ctypes as C
import json
import re
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import Renderer, U, I, look_at
from build import ROOT, SHADERS, shader_digest


def archive_source(archive):
    files={name[len('shaders/'):]:archive.read(name).decode('utf-8')
           for name in archive.namelist() if name.startswith('shaders/')}
    def expand(name):
        return re.sub(r'^\s*#include\s+"([^"]+)"\s*$',
                      lambda m:expand(m[1].lstrip('/')),files[name],flags=re.M)
    def source(path,options=None,pbr=False):
        text=expand(path.relative_to(SHADERS).as_posix())
        for name,value in (options or {}).items():
            text=re.sub(r'(^\s*#define\s+'+re.escape(name)+r'\s+)\S+',lambda m:m[1]+str(value),text,flags=re.M)
            text=re.sub(r'(^\s*const\s+(?:int|float)\s+'+re.escape(name)+r'\s*=\s*)[^;]+',lambda m:m[1]+str(value),text,flags=re.M)
        return text.replace('#version 330 compatibility\n','#version 330 compatibility\n#define IS_IRIS\n',1)
    return source


class TimedRenderer(Renderer):
    def __init__(self,*args):
        super().__init__(*args)
        self.stage='';self.samples={};self.measure=False
        self.query=U()
        self.call('glGenQueries',None,[I,C.POINTER(U)],1,C.byref(self.query))
    def use(self,name,*args):
        self.stage=name
        return super().use(name,*args)
    def timed(self,draw):
        if not self.measure:return draw()
        self.call('glBeginQuery',None,[U,U],0x88BF,self.query.value)
        draw()
        self.call('glEndQuery',None,[U],0x88BF)
        ns=C.c_uint64()
        self.call('glGetQueryObjectui64v',None,[U,U,C.POINTER(C.c_uint64)],self.query.value,0x8866,C.byref(ns))
        self.samples.setdefault(self.stage,[]).append(ns.value/1e6)
    def full_screen(self):
        return self.timed(super().full_screen)
    def quad(self,*args,**kwargs):
        draw=lambda:super(TimedRenderer,self).quad(*args,**kwargs)
        if self.stage=='gbuffers_water':return self.timed(draw)
        return draw()
    def close(self):
        self.call('glDeleteQueries',None,[I,C.POINTER(U)],1,C.byref(self.query))
        super().close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=str,default='Galaxy Shader-1.11.1.zip')
    args=parser.parse_args()
    with zipfile.ZipFile(ROOT/args.baseline) as archive:old=archive_source(archive)
    current=render_smoke.source_for
    renderer=TimedRenderer(1280,720)
    caches={'before':{},'after':{}}
    scene=renderer.scene;rotation=renderer.rotation.copy()
    results={};images=[]
    report={'type':'1280x720 HIGH synthetic GPU draw timings; not Minecraft FPS',
            'gpu':renderer.gl.info,'baseline':args.baseline,'shader_sha256':shader_digest()}
    cases=[('clouds','day',True,[0.6,0.6,-0.8]),('sunset','sunset',True,[0.3,0.12,-1.0]),
           ('day','day',False,None),('rain','rain',False,None),('underwater','underwater',False,None)]
    try:
        for label,kind,sky,sun in cases:
            renderer.scene=(lambda program,kind:None) if sky else scene
            renderer.rotation=look_at(np.zeros(3),np.array([0.0,0.55,-1.0])) if sky else rotation
            timings={'before':{},'after':{}};frames={}
            # Reverse order in the second round to limit clock/thermal bias.
            for variant in ['before','after','after','before']:
                render_smoke.source_for=old if variant=='before' else current
                renderer.programs=caches[variant]
                renderer.measure=False
                for frame in range(10):
                    im,_=renderer.render(kind,time=frame/30.0,sun_direction=sun,preserve_history=frame>0)
                frames[variant]=im
                renderer.measure=True;renderer.samples={}
                for frame in range(8):
                    renderer.render(kind,time=0.3,sun_direction=sun,preserve_history=True)
                for name,samples in renderer.samples.items():timings[variant].setdefault(name,[]).extend(samples)
            medians={variant:{name:float(np.median(values)) for name,values in stages.items()}
                     for variant,stages in timings.items()}
            delta=np.abs(np.asarray(frames['before'],float)-np.asarray(frames['after'],float))
            before=sum(medians['before'].values());after=sum(medians['after'].values())
            result={'gpu_ms':medians,'measured_draw_sum_ms':{'before':before,'after':after},
                    'draw_time_reduction_percent':100*(1-after/before),
                    'mean_abs_8bit_difference':float(delta.mean()),'p95_abs_8bit_difference':float(np.percentile(delta,95))}
            results[label]=result
            for variant,im in frames.items():im.save(ROOT/f'validation/perf-{label}-{variant}.png')
            images.append((label,frames))
            print(label+': '+json.dumps(result),flush=True)
            assert delta.mean()<3.0 and np.percentile(delta,95)<12, 'Visual change needs review: '+label
    finally:
        render_smoke.source_for=current
        renderer.programs={('variant',variant,*key):value for variant,cache in caches.items() for key,value in cache.items()}
        renderer.close()
    report['scenarios']=results
    report['status']='passed'
    (ROOT/'validation/performance-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    sheet=Image.new('RGB',(1280,390*len(images)),(14,17,21));draw=ImageDraw.Draw(sheet)
    for row,(label,frames) in enumerate(images):
        for col,variant in enumerate(['before','after']):
            sheet.paste(frames[variant].resize((640,360)),(col*640,row*390+30))
            draw.text((col*640+12,row*390+8),f'SYNTHETIC / {label.upper()} / {variant.upper()}',fill=(230,230,230))
    sheet.save(ROOT/'validation/performance-comparison.png')


if __name__=='__main__':main()
