"""Render the anthelion spot on the parhelic circle for visual review.

The fixture draws a simplified twilight sky and samples the authored
companion-halo function. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 360
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 6.0


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/ice_halo_extras.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(115.0 + 130.0 * uv.x);
    float el = radians(14.0 + 18.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.20, 0.24, 0.38), vec3(0.025, 0.055, 0.22),
                   smoothstep(0.15, 0.75, sin(el)));
    sky += vec3(0.05, 0.055, 0.07) * exp(-sin(el) * 10.0);
    vec3 halos = iceHaloCompanions(ray, sun, 1.0);
    sky += halos * ''' + str(GAIN) + ''';
    gl_FragColor = vec4(pow(max(sky, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun',
                     [np.cos(np.deg2rad(22.0)), np.sin(np.deg2rad(22.0)), 0.0])
    renderer.full_screen()
    renderer.check('anthelion panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'ANTHELION ON THE PARHELIC CIRCLE / SUN AT 22 DEG, '
              'ANTI-SOLAR POINT CENTRED / SYNTHETIC GPU PREVIEW (6x GAIN)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'anthelion.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 22.0,
        'azimuth_window_degrees': [115.0, 245.0],
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/anthelion.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'anthelion-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
