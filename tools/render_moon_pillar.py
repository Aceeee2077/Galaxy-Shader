"""Render a synthetic lunar ice pillar for visual review.

The fixture draws a night sky and samples the authored ice-halo function with
the lunar branch at a low moon. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 380
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/ice_halo.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testMoon;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-55.0 + 110.0 * uv.x);
    float el = radians(-5.0 + 45.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 moon = normalize(testMoon);
    vec3 sky = mix(vec3(0.020, 0.032, 0.055), vec3(0.004, 0.007, 0.016),
                   smoothstep(-0.02, 0.55, sin(el)));
    float disk = smoothstep(cos(radians(1.1)), cos(radians(0.9)),
                           dot(ray, moon));
    sky += vec3(0.85, 0.90, 1.0) * disk * 2.2;
    sky += vec3(0.10, 0.13, 0.20) * exp(-pow(acos(clamp(dot(ray, moon), -1.0, 1.0)) / 0.05, 2.0));
    vec3 halo = iceHalo(ray, moon, 1.0, vec3(0.74, 0.82, 1.0), 1.0);
    gl_FragColor = vec4(pow(max(sky + halo * 3.2, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testMoon', [np.cos(0.122), np.sin(0.122), 0.0])
    renderer.full_screen()
    renderer.check('lunar pillar panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'LUNAR ICE PILLAR / MOON AT 7 DEG / SYNTHETIC GPU '
              'PREVIEW (3.2x GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'moon-pillar.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'moon_elevation_degrees': 7.0,
        'preview_gain': 3.2,
        'preview': 'Galaxy Shader/previews/moon-pillar.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'moon-pillar-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
