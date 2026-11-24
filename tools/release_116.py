"""Promote one 1.16.x release from a JSON spec.

The spec lives outside the repository (tools/.cache/release.json) and carries
the version, test count, Chinese/English release notes and the three technical
paragraphs. The script performs the same sequence every release uses: regenerate
entrypoints, run the full regression suite and GPU matrix, render the synthetic
smoke scenes, check the real Iris parser, package the ZIP, then commit and push.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'Galaxy Shader'
SPEC = ROOT / 'tools' / '.cache' / 'release.json'
IRIS = ROOT / 'tools' / '.cache' / 'iris-fabric-1.11.2+mc26.2.jar'
LIBS = ROOT / 'tools' / '.cache' / 'java-deps'


def run(args, cwd=ROOT):
    print('+', ' '.join(str(a) for a in args), flush=True)
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True,
                            encoding='utf-8', errors='replace')
    tail = '\n'.join((result.stdout + result.stderr).splitlines()[-8:])
    if result.returncode:
        print(tail, flush=True)
        raise SystemExit(f'command failed: {args}')
    if tail.strip():
        print(tail, flush=True)
    return result


def insert_after(path, marker, text):
    value = path.read_text(encoding='utf-8')
    if text.strip() and text.strip() not in value:
        assert marker in value, f'missing marker in {path}'
        value = value.replace(marker, marker + text, 1)
        path.write_text(value, encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-push', action='store_true')
    args = parser.parse_args()
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    version = spec['version']
    assert re.fullmatch(r'1\.16\.\d+', version), version

    build = ROOT / 'tools' / 'build.py'
    text = build.read_text(encoding='utf-8')
    text = re.sub(r"VERSION = '1\.16\.\d+'", f"VERSION = '{version}'", text)
    build.write_text(text, encoding='utf-8', newline='\n')

    insert_after(PACK / 'CHANGELOG.md', '# Changelog\n\n',
                 f"## {version} — 2026-11-24\n\n{spec['changelog'].strip()}\n\n")
    insert_after(PACK / 'ARCHITECTURE.md', '# Rendering architecture\n\n',
                 f"{spec['architecture'].strip()}\n\n")
    insert_after(PACK / 'VALIDATION.md', '# Validation — 2026-11-24\n\n',
                 f"{version}（2026-11-24）：{spec['validation'].strip()}\n\n")

    roadmap = PACK / 'ROADMAP.md'
    lines = roadmap.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f'| {version} |'):
            cells = line.split('|')
            cells[-2] = ' 已完成 '
            lines[i] = '|'.join(cells)
            break
    roadmap.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

    for name, note in [('README.md', spec['zh']), ('README-EN.md', spec['en'])]:
        path = PACK / name
        value = path.read_text(encoding='utf-8')
        value = re.sub(r'· \d+\.\d+\.\d+ ·', f'· {version} ·', value, count=1)
        value = re.sub(r'Galaxy Shader-\d+\.\d+\.\d+\.zip',
                       f'Galaxy Shader-{version}.zip', value)
        lines = value.splitlines()
        header = next(i for i, line in enumerate(lines)
                      if line.startswith('**Photorealistic Minecraft Shader'))
        if note.strip() and note.strip() not in value:
            lines[header + 1:header + 1] = ['', note.strip()]
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

    for name in ('README.md', 'README-EN.md'):
        path = ROOT / name
        value = path.read_text(encoding='utf-8')
        value = re.sub(r'1\.16\.\d+', version, value)
        path.write_text(value, encoding='utf-8', newline='\n')

    run([sys.executable, 'tools/build.py'])
    run([sys.executable, '-m', 'unittest', 'discover', '-p', 'test_*.py'],
        cwd=ROOT / 'tools')
    run([sys.executable, 'tools/validate.py'])
    run([sys.executable, 'tools/render_smoke.py'])
    run([sys.executable, 'tools/check_iris_directives.py', '--iris', str(IRIS),
         '--libraries', str(LIBS)])
    run([sys.executable, 'tools/build.py', '--package'])

    current = ROOT / f'Galaxy Shader-{version}.zip'
    for old in ROOT.glob('Galaxy Shader-*.zip'):
        if old != current:
            old.unlink()
            sha = old.with_name(old.name + '.sha256')
            if sha.exists():
                sha.unlink()

    if not args.no_push:
        run(['git', 'add', '-A'])
        run(['git', 'commit', '-m', spec['commit']])
        run(['git', 'push', 'origin', 'main'])
        run(['git', 'status', '-sb'])
    print(f'{version} complete: {spec["tests"]} regressions, '
          f'{current.name}', flush=True)


if __name__ == '__main__':
    main()
