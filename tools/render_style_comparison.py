"""Review a visual redesign against an exact source ZIP, on the actual GPU.

Images and elapsed draw queries use synthetic fixtures, not Minecraft gameplay.
Unlike the performance-only comparator, intentional visual differences are not
treated as errors. Keep the paired images for human review.
"""
import argparse
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import look_at
from compare_performance import TimedRenderer, archive_source
from build import ROOT, shader_digest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',default='tools/.cache/photon-style-before.zip')
    args=parser.parse_args()
    with zipfile.ZipFile(ROOT/args.baseline) as archive:
        old=archive_source(archive)
    current=render_smoke.source_for
    renderer=TimedRenderer(960,540)
    scene=renderer.scene
    rotation=renderer.rotation.copy()
    caches={'before':{},'after':{}}
    report={'type':'Synthetic GPU style comparison; not Minecraft gameplay or FPS',
            'gpu':renderer.gl.info,'baseline':args.baseline,
            'shader_sha256':shader_digest(),'scenarios':{}}
    cases=[('noon','day',False,None),
           ('morning-clouds','day',True,[0.3,0.12,-1.0]),
           ('noon-clouds','day',True,[0.6,0.6,-0.8]),
           ('sunset','sunset',False,[-0.4,0.12,-1.0]),
           ('rain','rain',False,None),('night','night',False,None),
           ('underwater','underwater',False,None)]
    images=[]
    try:
        for label,kind,sky,sun in cases:
            renderer.scene=(lambda p,k:None) if sky else scene
            renderer.rotation=look_at(np.zeros(3),np.array([0.0,0.55,-1.0])) if sky else rotation
            frames={}
            timings={'before':{},'after':{}}
            # Alternate A/B/B/A to limit thermal/clock bias in draw timings.
            for variant in ['before','after','after','before']:
                render_smoke.source_for=old if variant=='before' else current
                renderer.programs=caches[variant]
                renderer.measure=False
                for frame in range(12):
                    im,_=renderer.render(kind,time=frame/30.0,sun_direction=sun,
                                         preserve_history=frame>0)
                frames[variant]=im
                renderer.measure=True
                renderer.samples={}
                for frame in range(4):
                    renderer.render(kind,time=0.4,sun_direction=sun,preserve_history=True)
                for name,values in renderer.samples.items():
                    timings[variant].setdefault(name,[]).extend(values)
            medians={v:{stage:float(np.median(values)) for stage,values in stages.items()}
                     for v,stages in timings.items()}
            delta=np.abs(np.asarray(frames['before'],float)-np.asarray(frames['after'],float))
            report['scenarios'][label]={
                'mean_abs_8bit_difference':float(delta.mean()),
                'p95_abs_8bit_difference':float(np.percentile(delta,95)),
                'gpu_draw_ms':medians,
                'measured_draw_sum_ms':{v:sum(stages.values()) for v,stages in medians.items()}}
            for variant,im in frames.items():
                im.save(ROOT/f'validation/style-{label}-{variant}.png')
            images.append((label,frames))
            print(label+': '+json.dumps(report['scenarios'][label]),flush=True)
    finally:
        render_smoke.source_for=current
        renderer.programs={('variant',variant,*key):value
                           for variant,cache in caches.items() for key,value in cache.items()}
        renderer.close()
    sheet=Image.new('RGB',(1280,390*len(images)),(14,17,21))
    draw=ImageDraw.Draw(sheet)
    for row,(label,frames) in enumerate(images):
        for col,variant in enumerate(['before','after']):
            sheet.paste(frames[variant].resize((640,360)),(col*640,row*390+30))
            draw.text((col*640+12,row*390+8),
                      f'SYNTHETIC / {label.upper()} / {variant.upper()}',fill=(230,230,230))
    sheet.save(ROOT/'validation/style-comparison.png')
    report['status']='rendered for visual review'
    (ROOT/'validation/style-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
