"""Validate includes, settings, buffers and actual OpenGL shader compilation."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import time
from build import ROOT, SHADERS, PROFILES, PROFILE_KEYS, PROGRAMS, SCREENS, shader_digest

def expand(path, stack=()):
    path=path.resolve()
    assert path.is_relative_to(SHADERS.resolve()), f'Include outside pack: {path}'
    assert path not in stack, f'Cyclic include: {path}'
    source=path.read_text(encoding='utf-8')
    def include(match):
        name=match.group(1)
        target=SHADERS/name[1:] if name.startswith('/') else path.parent/name
        assert target.is_file(),f'Missing include {name} in {path}'
        return expand(target,(*stack,path))
    return re.sub(r'^\s*#include\s+"([^"]+)"\s*$',include,source,flags=re.M)

def source_for(path,options=None,pbr=False):
    source=expand(path)
    for name,value in (options or {}).items():
        source=re.sub(r'(^\s*#define\s+'+re.escape(name)+r'\s+)\S+',lambda m:m[1]+str(value),source,flags=re.M)
        source=re.sub(r'(^\s*const\s+(?:int|float)\s+'+re.escape(name)+r'\s*=\s*)[^;]+',lambda m:m[1]+str(value),source,flags=re.M)
    # Only emulate loader environment macros. Never supply missing pack symbols.
    preamble='#define IS_IRIS\n'
    if pbr: preamble+='#define MC_TEXTURE_FORMAT_LAB_PBR 1\n'
    return source.replace('#version 330 compatibility\n','#version 330 compatibility\n'+preamble,1)

def validate_clear_colors(source):
    for name,args in re.findall(r'const\s+vec4\s+(colortex\d+ClearColor)\s*=\s*vec4\(([^)]*)\)',source):
        components=[v.strip() for v in args.split(',')]
        assert len(components)==4,f'Iris requires four components: {name}'
        for component in components: float(component)

def static_checks():
    files=list(SHADERS.rglob('*'))
    shaders=[p for p in files if p.suffix in ['.vsh','.fsh'] and p.parent.name!='program']
    for path in files:
        if not path.is_file(): continue
        text=path.read_text(encoding='utf-8')
        assert text.strip(),f'Empty file {path}'
        assert not re.search(r'\b(TODO|FIXME|placeholder)\b|not implemented',text,re.I),str(path)
    for path in shaders:
        expanded=expand(path)
        # Iris's CPU directive parser does not implement GLSL scalar splats.
        # A legal vec4(0.0) shader expression crashes older Iris here.
        validate_clear_colors(expanded)
        assert expanded.count('#version')==1,str(path)
        assert path.with_suffix('.fsh' if path.suffix=='.vsh' else '.vsh').exists()
        if path.suffix=='.fsh' and path.stem!='final':
            targets=re.findall(r'/\* DRAWBUFFERS:(\d+) \*/',expanded)
            assert len(targets)==1,(path,targets)
            assert all(int(x)<=7 for x in targets[0]),str(path)
    settings=(SHADERS/'lib/settings.glsl').read_text()
    options={}
    for line in settings.splitlines():
        m=re.search(r'(?:#define\s+(\w+)\s+(\S+)|const\s+(?:int|float)\s+(\w+)\s*=\s*([^;]+);).*//\s*\[([^]]+)\]',line)
        if m: options[m[1] or m[3]]={'default':m[2] or m[4],'values':m[5].split()}
    for name,values in PROFILES.items():
        for key,val in zip(PROFILE_KEYS,values):
            assert str(val) in options[key]['values'],(name,key,val)
    for key,val in zip(PROFILE_KEYS,PROFILES['HIGH']):
        assert options[key]['default']==str(val),(key,options[key])
    for screen,names in SCREENS.items():
        for name in names.split(): assert name in options,(screen,name)
    properties=(SHADERS/'shaders.properties').read_text()
    keys=[line.split('=',1)[0] for line in properties.splitlines() if line and not line.startswith('#')]
    assert len(keys)==len(set(keys)),'Duplicate properties'
    assert set(options)==set(' '.join(SCREENS.values()).split()),'Unreachable menu option'
    for lang in ['en_us','zh_cn']:
        labels=(SHADERS/'lang'/f'{lang}.lang').read_text(encoding='utf-8')
        for option in options: assert f'option.{option}=' in labels
    # Match aliases to a real source implementation, and dimensions to their define.
    for folder,dim in [('',0),('world0',0),('world-1',-1),('world1',1)]:
        for name in PROGRAMS:
            assert f'#define DIMENSION {dim}' in (SHADERS/folder/f'{name}.fsh').read_text()
    return {'entrypoint_files':len(shaders),'options':len(options),'profiles':list(PROFILES),'static':'passed'},options

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--static-only',action='store_true')
    parser.add_argument('--quick',action='store_true')
    args=parser.parse_args()
    started=time.time(); report,option_definitions=static_checks()
    if not args.static_only:
        from gl_context import GLContext
        gl=GLContext(); report['gpu']=gl.info
        print(json.dumps(gl.info),flush=True)
        configs={name:dict(zip(PROFILE_KEYS,values)) for name,values in PROFILES.items()}
        if args.quick: configs={'HIGH':configs['HIGH']}
        else:
            configs['ALL_OFF']={k:'0' for k,v in option_definitions.items() if '0' in v['values']}
            configs['FORCE_PBR_MOTION']={'PBR_MODE':2,'MOTION_BLUR':3,'DOF_QUALITY':3}
        cache=set(); count=0; cases=0
        try:
            for folder in ['', 'world0','world-1','world1']:
                for profile,options in configs.items():
                    for pbr in [False,True]:
                        for name in PROGRAMS:
                            vs=source_for(SHADERS/folder/f'{name}.vsh',options,pbr)
                            fs=source_for(SHADERS/folder/f'{name}.fsh',options,pbr)
                            key=hashlib.sha256((vs+fs).encode()).hexdigest(); cases+=1
                            if key in cache: continue
                            try: program=gl.compile(vs,fs)
                            except Exception:
                                out=ROOT/'validation'/'expanded'; out.mkdir(parents=True,exist_ok=True)
                                (out/'failed.vert').write_text(vs)
                                (out/'failed.frag').write_text(fs)
                                print(f'FAILED {folder}/{name} {profile} PBR={pbr}',flush=True)
                                raise
                            gl.delete_program(program); count+=1; cache.add(key)
                    print(f'Compiled {folder or "root"} / {profile}: {count} unique pairs',flush=True)
        finally: gl.close()
        report.update(driver_compile='passed',linked_unique_programs=count,entrypoint_configuration_pairs=cases)
    report['seconds']=round(time.time()-started,2)
    report['shader_sha256']=shader_digest()
    report['full_matrix']=not args.quick and not args.static_only
    report['game_validation']='User logs reproduced clear-color parsing and undefined format-token failures. Both fixed; full gameplay acceptance remains pending.'
    output=ROOT/'validation'; output.mkdir(exist_ok=True)
    (output/'compile-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__': main()
