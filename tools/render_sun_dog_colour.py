"""Render a synthetic close-up of the right sun dog for visual review.

The fixture draws a low-sun daytime sky and samples the authored halo function
at a 7-degree sun. It is not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/ice_halo.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(16.0 + 12.0 * uv.x);
    float el = radians(4.0 + 6.5 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.30, 0.42, 0.62), vec3(0.14, 0.26, 0.50),
                   smoothstep(0.02, 0.20, sin(el)));
    sky += vec3(0.22, 0.17, 0.11) * exp(-pow(acos(clamp(dot(ray, sun), -1.0, 1.0)) / 0.24, 2.0));
    vec3 halo = iceHalo(ray, sun, 1.0, vec3(1.0, 0.94, 0.84), 0.0);
    gl_FragColor = vec4(pow(max(sky + halo * 4.0, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    elevation = np.deg2rad(7.0)
    renderer.uniform(program, 'testSun',
                     [np.cos(elevation), np.sin(elevation), 0.0])
    renderer.full_screen()
    renderer.check('sun dog colour close-up')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'RIGHT SUN DOG / RED INNER FLANK TO BLUE OUTER FLANK / '
              'SUN AT 7 DEG / SYNTHETIC GPU PREVIEW (4x GAIN)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'sun-dog-colour.png')

    report = {
        'type': 'Synthetic GPU close-up; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 7.0,
        'field_degrees': {'azimuth': [16.0, 28.0], 'elevation': [4.0, 10.5]},
        'preview_gain': 4.0,
        'preview': 'Galaxy Shader/previews/sun-dog-colour.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'sun-dog-colour-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
