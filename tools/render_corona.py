"""Render a synthetic lunar corona for visual review.

The fixture draws a night sky, a moon disk and the authored diffraction rings.
It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 520
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/corona.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testMoon;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-60.0 + 120.0 * uv.x);
    float el = radians(0.0 + 50.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 moon = normalize(testMoon);
    vec3 sky = mix(vec3(0.010, 0.016, 0.038), vec3(0.028, 0.044, 0.085),
                   smoothstep(0.0, 0.70, sin(el)));
    float moonAngle = acos(clamp(dot(ray, moon), -1.0, 1.0));
    float disk = 1.0 - smoothstep(0.0080, 0.0105, moonAngle);
    sky += vec3(1.0, 0.97, 0.88) * disk * 2.4;
    sky += vec3(0.90, 0.94, 1.0) * exp(-moonAngle / 0.030) * 0.16;
    vec3 rings = lunarCorona(ray, moon, 1.0, 0.0, 1.0) * 3.0;
    gl_FragColor = vec4(pow(max(sky + rings, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testMoon',
                     [np.cos(0.436), np.sin(0.436), 0.0])
    renderer.full_screen()
    renderer.check('lunar corona preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'LUNAR CORONA / MOON AT 25 DEG / '
              'SYNTHETIC GPU PREVIEW (RINGS 3x)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'lunar-corona.png')

    report = {
        'type': 'Synthetic GPU night panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'moon_elevation_degrees': 25.0,
        'preview_gain': 'rings 3x',
        'preview': 'Galaxy Shader/previews/lunar-corona.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'lunar-corona-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
