"""Render a synthetic before/after panorama of the noctilucent wave trains.

The left half samples NLC_WAVES off and the right half on; the cloud layer is
brightened for review. It is not a Minecraft screenshot.
"""
import json
import re
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 1200, 360
GAIN = 5.0
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def fragment(waves):
    common = expand(SHADERS / 'lib/common.glsl')
    common = re.sub(r'^\s*#define\s+NLC_WAVES\s+\S+',
                    f'#define NLC_WAVES {waves}', common, flags=re.M)
    return ('#version 330 compatibility\n' + common +
            expand(SHADERS / 'lib/noctilucent.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.62;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 base = mix(vec3(0.008, 0.012, 0.024), vec3(0.018, 0.028, 0.048),
                    smoothstep(0.0, 0.8, uv.y));
    vec3 cloud = noctilucentClouds(ray, normalize(testSun), 0.0, 1.0) * 5.0;
    gl_FragColor = vec4(pow(max(base * 0.35 + cloud, 0.0), vec3(1.0 / 2.2)),
                        1.0);
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
        renderer.uniform(program, 'testSun', [0.984, -0.18, 0.0])
        renderer.uniform(program, 'frameTimeCounter', 120.0)
        renderer.full_screen()
        renderer.check('noctilucent waves preview')
        panels[state] = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0,
                                0, 255)
    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    # Both panels show the same sky quadrant so only the wave trains differ.
    pixels = np.concatenate([panels[0][:, :W // 2],
                             panels[1][:, :W // 2]], axis=1)
    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'NOCTILUCENT CLOUDS / SMOOTH VEIL (LEFT) VS CROSSED '
              'GRAVITY-WAVE TRAINS (RIGHT) / SYNTHETIC GPU PANORAMA (GAIN)',
              fill=(225, 228, 235))
    draw.text((8, H + 8), 'NLC_WAVES = 0', fill=(190, 198, 210))
    draw.text((W // 2 + 8, H + 8), 'NLC_WAVES = 1', fill=(190, 198, 210))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'nlc-waves.png')

    report = {
        'type': 'Synthetic GPU panorama pair; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_height': -0.18,
        'summer': 1.0,
        'preview_gain': GAIN,
        'panels': ['NLC_WAVES=0', 'NLC_WAVES=1'],
        'preview': 'Galaxy Shader/previews/nlc-waves.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'nlc-waves-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
