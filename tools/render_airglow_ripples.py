"""Render a synthetic panorama of the banded night airglow.

The fixture samples airglow() over an upper-hemisphere strip and brightens it
for review. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 1200, 520
GAIN = 8.0
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/twilight_optics.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.62;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 sky = mix(vec3(0.009, 0.014, 0.030), vec3(0.003, 0.005, 0.014),
                   smoothstep(0.0, 0.9, uv.y));
    sky += airglow(ray, normalize(testSun)) * 8.0;
    gl_FragColor = vec4(pow(max(sky, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse',
                     np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [0.0, -0.80, 1.0])
    renderer.uniform(program, 'frameTimeCounter', 40.0)
    renderer.full_screen()
    renderer.check('airglow ripples preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'AIRGLOW GRAVITY-WAVE BANDS / FAINT HORIZONTAL '
              'RIPPLES / SYNTHETIC GPU PREVIEW (8x GAIN)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'airglow-ripples.png')

    report = {
        'type': 'Synthetic GPU airglow panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'gain': GAIN,
        'preview_note': 'night airglow brightened 8x for review',
        'preview': 'Galaxy Shader/previews/airglow-ripples.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'airglow-ripples-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
