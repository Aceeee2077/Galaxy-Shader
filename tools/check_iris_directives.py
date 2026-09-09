"""Run the real CPU directive parser from one or more installed Iris JARs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from build import ROOT, SHADERS, shader_digest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iris',type=Path,action='append',required=True)
    parser.add_argument('--libraries',type=Path,required=True)
    parser.add_argument('--java',default=shutil.which('java') or 'java')
    args=parser.parse_args()
    dependencies=[]
    for pattern in ['joml-*.jar','fastutil-*.jar','guava-*.jar','slf4j-api-*.jar']:
        matches=sorted(args.libraries.rglob(pattern))
        if not matches:raise FileNotFoundError(f'Missing dependency: {pattern}')
        dependencies.append(matches[-1])
    results=[]
    for jar in args.iris:
        if not jar.is_file(): raise FileNotFoundError(jar)
        with zipfile.ZipFile(jar) as archive:
            nested=next(n for n in archive.namelist() if n.startswith('META-INF/jars/jcpp-') and n.endswith('.jar'))
            jcpp=ROOT/'tools/.cache/java-deps'/Path(nested).name
            jcpp.parent.mkdir(parents=True,exist_ok=True)
            jcpp.write_bytes(archive.read(nested))
        classpath=os.pathsep.join(str(p.resolve()) for p in [jar,*dependencies,jcpp])
        run=subprocess.run([args.java,'-cp',classpath,str(ROOT/'tools/IrisDirectiveCheck.java'),
                            str(SHADERS/'lib/buffers.glsl')],capture_output=True,text=True,encoding='utf-8')
        if run.returncode: raise RuntimeError(run.stdout+run.stderr)
        assert 'PASS:' in run.stdout
        print(jar.name+': '+run.stdout.strip(),flush=True)
        results.append({'iris':jar.name,'status':'passed','result':run.stdout.strip()})
    report={'shader_sha256':shader_digest(),'status':'passed','parser_versions':results,
            'scope':'Actual Iris GLSL preprocessor, render-target format and clear-color parsers; not full gameplay.'}
    (ROOT/'validation/iris-directive-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

if __name__=='__main__':main()
