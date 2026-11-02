"""Render a synthetic parhelic circle for visual review.

The fixture draws a simplified clear sky and samples the authored companion
halo function at a low sun, where the white horizontal parhelic circle is most
visible. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 360
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


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
    float az = radians(-90.0 + 180.0 * uv.x);
    float el = radians(42.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.36, 0.43, 0.56), vec3(0.07, 0.19, 0.50),
                   smoothstep(0.0, 0.70, sin(el)));
    vec3 halos = iceHaloCompanions(ray, sun, 1.0);
    gl_FragColor = vec4(pow(max(sky + halos * 2.4, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [np.cos(0.30), np.sin(0.30), 0.0])
    renderer.full_screen()
    renderer.check('parhelic circle panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'PARHELIC CIRCLE / SUN AT 17 DEG / SYNTHETIC GPU PREVIEW '
              '(2.4x GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'parhelic-circle.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 17.2,
        'preview_gain': 2.4,
        'preview': 'Galaxy Shader/previews/parhelic-circle.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'parhelic-circle-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
