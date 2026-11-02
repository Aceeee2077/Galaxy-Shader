"""Render a synthetic before/after view of the auroral curtain folds.

The left panel has AURORA_FOLDS off and the right panel on; both show the same
northern sky. It is not a Minecraft screenshot.
"""
import json
import re
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 1200, 380
GAIN = 3.2
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def fragment(folds):
    common = expand(SHADERS / 'lib/common.glsl')
    common = re.sub(r'^\s*#define\s+AURORA_FOLDS\s+\S+',
                    f'#define AURORA_FOLDS {folds}', common, flags=re.M)
    return ('#version 330 compatibility\n' + common +
            expand(SHADERS / 'lib/night_sky.glsl') +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 1.45;
    float elevation = uv.y * 0.55;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 base = mix(vec3(0.006, 0.010, 0.022), vec3(0.002, 0.004, 0.010),
                    smoothstep(0.0, 0.8, uv.y));
    vec3 colour = base + auroraSky(ray, 1.0) * 3.2;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {state: renderer.gl.compile(VERTEX, fragment(state))
                for state in (0, 1)}
    renderer.bind_fbo([renderer.final])
    panels = {}
    for state, program in programs.items():
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'frameTimeCounter', 70.0)
        renderer.full_screen()
        renderer.check('aurora folds preview')
        panels[state] = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0,
                                0, 255)
    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    pixels = np.concatenate([panels[0][:, :W // 2],
                             panels[1][:, :W // 2]], axis=1)
    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'AURORA CURTAIN / FLAT RIBBON (LEFT) VS HANGING PLEATS '
              '(RIGHT) / SYNTHETIC GPU VIEW (GAIN)', fill=(225, 228, 235))
    draw.text((8, H + 8), 'AURORA_FOLDS = 0', fill=(190, 198, 210))
    draw.text((W // 2 + 8, H + 8), 'AURORA_FOLDS = 1',
              fill=(190, 198, 210))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'aurora-folds.png')

    report = {
        'type': 'Synthetic GPU panorama pair; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_gain': GAIN,
        'panels': ['AURORA_FOLDS=0', 'AURORA_FOLDS=1'],
        'preview': 'Galaxy Shader/previews/aurora-folds.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'aurora-folds-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
