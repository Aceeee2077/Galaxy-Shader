"""Render a synthetic meteor persistent train for visual review.

The fixture draws the authored meteor path and its afterglow against a night
sky. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 500
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/meteor_train.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testHead;
uniform vec3 testTail;
uniform float testLife;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-60.0 + 120.0 * uv.x);
    float el = radians(5.0 + 60.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 head = normalize(testHead);
    vec3 tail = normalize(testTail);
    vec3 sky = mix(vec3(0.020, 0.034, 0.058), vec3(0.003, 0.006, 0.014),
                   smoothstep(0.05, 0.70, sin(el)));
    float headGlow = pow(max(dot(ray, head), 0.0), 1600.0);
    float streak = 1.0 - smoothstep(0.0, 0.010,
                                    acos(clamp(dot(ray, head), -1.0, 1.0)));
    vec3 meteor = vec3(0.62, 0.82, 1.0) * (headGlow * 2.2 +
                   streak * 0.35);
    vec3 train = meteorTrain(ray, head, tail, testLife, 0.37, 1.2);
    gl_FragColor = vec4(pow(max(sky + meteor + train * 6.0, 0.0),
                            vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    head = np.array([np.cos(0.61) * np.cos(0.35), np.sin(0.61),
                     np.cos(0.61) * np.sin(0.35)])
    tail = head - np.array([-0.25, -0.55, 0.12]) * 0.55
    tail /= np.linalg.norm(tail)
    head /= np.linalg.norm(head)
    renderer.uniform(program, 'testHead', head.tolist())
    renderer.uniform(program, 'testTail', tail.tolist())
    renderer.uniform(program, 'testLife', 1.0)
    renderer.full_screen()
    renderer.check('meteor train panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'METEOR PERSISTENT TRAIN / AFTERGLOW ALONG THE PATH / '
              'SYNTHETIC GPU PREVIEW (6x GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'meteor-train.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_gain': 6.0,
        'preview': 'Galaxy Shader/previews/meteor-train.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'meteor-train-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
