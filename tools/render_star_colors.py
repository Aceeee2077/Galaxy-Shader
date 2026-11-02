"""Render a synthetic star field with colour temperature for visual review.

The fixture draws enlarged stars against a night sky and samples the authored
starColour mapping. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 540
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/noise.glsl') +
                expand(SHADERS / 'lib/star_color.glsl') +
                '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 sky = mix(vec3(0.012, 0.020, 0.040), vec3(0.003, 0.005, 0.012),
                   smoothstep(0.0, 0.8, uv.y));
    vec2 starUV = uv * vec2(96.0, 54.0);
    vec2 cell = floor(starUV);
    float presence = hash12(cell);
    float magnitude = hash12(cell + 57.1);
    float temperature = hash12(cell + 31.7);
    vec2 jitter = 0.25 + 0.50 * vec2(hash12(cell + 3.1), hash12(cell + 7.9));
    vec2 delta = fract(starUV) - jitter;
    float core = pow(max(1.0 - length(delta) * 3.0, 0.0),
                     mix(2.0, 6.0, magnitude));
    float star = step(0.60, presence) * core * mix(0.45, 1.5, magnitude);
    float glow = exp(-length(delta) * 9.0) * star * 0.35;
    vec3 colour = starColour(magnitude, temperature) * (star + glow) * 1.6;
    gl_FragColor = vec4(pow(max(sky + colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.full_screen()
    renderer.check('star colour preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'STELLAR COLOUR TEMPERATURE / WARM ORANGE TO COOL '
              'BLUE-WHITE / SYNTHETIC GPU PREVIEW (ENLARGED STARS)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'star-colors.png')

    report = {
        'type': 'Synthetic GPU star field; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_note': 'stars enlarged for review',
        'preview': 'Galaxy Shader/previews/star-colors.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'star-colors-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
