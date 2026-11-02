"""Render the same star field at two instants for visual review.

The fixture draws a synthetic night sky twice, with identical star positions and
the authored scintillation factor sampled at two times. It is not a Minecraft
screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 420
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/noise.glsl') +
                expand(SHADERS / 'lib/scintillation.glsl') +
                '''
uniform vec2 testResolution;
void main() {
    vec2 p = gl_FragCoord.xy / testResolution;
    float panel = step(0.5, p.x);
    vec2 uv = vec2(fract(p.x * 2.0), p.y);
    float az = radians(-90.0 + 180.0 * uv.x);
    float el = radians(5.0 + 65.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec2 starUV = vec2(atan(ray.z, ray.x), asin(clamp(ray.y, -1.0, 1.0))) *
                  vec2(130.0, 90.0);
    float cell = hash12(floor(starUV));
    float star = step(0.988, cell) *
                 pow(max(1.0 - length(fract(starUV) - 0.5) * 2.0, 0.0), 3.0);
    float time = mix(0.0, 0.35, panel);
    float twinkle = starScintillation(hash12(floor(starUV) + 13.7), ray.y,
                                      time, 2.0);
    vec3 sky = mix(vec3(0.006, 0.010, 0.026), vec3(0.020, 0.034, 0.072),
                   smoothstep(0.0, 0.75, sin(el)));
    sky += vec3(star * twinkle * 1.8);
    if (abs(p.x - 0.5) < 0.0012) sky = vec3(0.55, 0.60, 0.70);
    gl_FragColor = vec4(pow(max(sky, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.full_screen()
    renderer.check('star scintillation preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'STAR SCINTILLATION / SAME FIELD AT t=0.00 s (LEFT) AND '
              't=0.35 s (RIGHT) / SYNTHETIC GPU PREVIEW (TWINKLE 2x)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'star-scintillation.png')

    report = {
        'type': 'Synthetic GPU night panorama pair; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sample_times_seconds': [0.0, 0.35],
        'preview_gain': 'twinkle 2x',
        'preview': 'Galaxy Shader/previews/star-scintillation.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'scintillation-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
