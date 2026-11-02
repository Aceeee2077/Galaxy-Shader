"""Render a synthetic comet with its sunward anti-tail for visual review.

The fixture draws the authored head, dust tail and anti-tail against a dark sky.
It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 900, 500
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/noise.glsl') +
                expand(SHADERS / 'lib/comet_antitail.glsl') +
                '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-165.0 + 110.0 * uv.x);
    float el = radians(5.0 + 55.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 head = normalize(vec3(-0.35, 0.30, -0.88));
    vec3 tailDir = normalize(vec3(0.30, -0.55, 0.35));
    float headGlow = pow(max(dot(ray, head), 0.0), 900.0);
    float tail = 0.0;
    for (int i = 0; i < 6; ++i) {
        float t = float(i) / 5.0;
        vec3 p = normalize(head + tailDir * t * 0.55);
        float d = acos(clamp(dot(ray, p), -1.0, 1.0));
        tail += (1.0 - smoothstep(0.0, 0.045 + t * 0.05, d)) * (1.0 - t);
    }
    vec3 sky = mix(vec3(0.004, 0.008, 0.020), vec3(0.014, 0.024, 0.048),
                   smoothstep(0.0, 0.70, sin(el)));
    vec3 comet = vec3(0.55, 0.72, 1.0) * headGlow * 1.0 +
                 vec3(0.35, 0.55, 0.85) * tail * 0.30 +
                 cometAntitail(ray, 1.0) * 8.0;
    gl_FragColor = vec4(pow(max(sky + comet, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.full_screen()
    renderer.check('comet anti-tail preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'COMET ANTI-TAIL / SUNWARD SPIKE OPPOSITE THE DUST TAIL / '
              'SYNTHETIC GPU PREVIEW (ANTI-TAIL 8x)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'comet-antitail.png')

    report = {
        'type': 'Synthetic GPU comet view; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_gain': 'anti-tail 8x',
        'preview': 'Galaxy Shader/previews/comet-antitail.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'comet-antitail-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
