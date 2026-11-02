"""Render a synthetic fog bow for visual review.

The fixture draws a grey fog sky with the sun 20 degrees behind the camera and
the authored broad anti-solar arc. It is not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/fogbow.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-120.0 + 240.0 * uv.x);
    float el = radians(0.0 + 55.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.52, 0.56, 0.60), vec3(0.30, 0.36, 0.44),
                   smoothstep(0.0, 0.80, sin(el)));
    vec3 bow = fogbow(ray, sun, 1.0, 1.0) * 2.2;
    gl_FragColor = vec4(pow(max(sky + bow, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    # The sun sits behind the camera, 20 degrees above the horizon.
    renderer.uniform(program, 'testSun',
                     [-np.cos(0.349), np.sin(0.349), 0.0])
    renderer.full_screen()
    renderer.check('fog bow preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'FOG BOW / SUN 20 DEG BEHIND CAMERA / '
              'SYNTHETIC GPU PREVIEW (BOW 2.2x)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'fogbow.png')

    report = {
        'type': 'Synthetic GPU fog panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 20.0,
        'view_elevation_degrees': [0.0, 55.0],
        'preview_gain': 'bow 2.2x',
        'preview': 'Galaxy Shader/previews/fogbow.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'fogbow-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
