"""Render a synthetic panorama of the analytic nacreous cloud sheet.

The fixture samples the authored sky function on an equirectangular dome with a
dim winter-twilight gradient. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 300
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/nacreous.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.80;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 sun = normalize(testSun);
    float horizon = pow(1.0 - clamp(ray.y, 0.0, 1.0), 3.0);
    vec3 base = mix(vec3(0.008, 0.012, 0.028), vec3(0.035, 0.045, 0.060),
                    horizon);
    base += vec3(0.08, 0.035, 0.018) * horizon * horizon;
    vec3 colour = base * 0.55 + nacreousClouds(ray, sun, 0.0, 1.0) * 3.0;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [0.995, -0.10, 0.0])
    renderer.uniform(program, 'frameTimeCounter', 120.0)
    renderer.full_screen()
    renderer.check('nacreous panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'NACREOUS CLOUDS / WINTER TWILIGHT / '
              'SYNTHETIC GPU PANORAMA (PREVIEW GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'nacreous.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_height': -0.10,
        'season': 'winter',
        'preview': 'Galaxy Shader/previews/nacreous.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'nacreous-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
