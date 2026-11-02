"""Render a synthetic panorama of the analytic 22-degree ice-crystal halo.

The fixture samples the authored halo function on an equirectangular dome with
a dim twilight gradient. It is not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/ice_halo.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.90;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 sun = normalize(testSun);
    float horizon = pow(1.0 - clamp(ray.y, 0.0, 1.0), 3.0);
    float sunward = pow(max(dot(normalize(vec3(ray.x, 0.0, ray.z)),
                               normalize(vec3(sun.x, 0.0, sun.z))), 0.0), 3.0);
    vec3 base = mix(vec3(0.010, 0.016, 0.038), vec3(0.055, 0.050, 0.055), horizon);
    base += vec3(0.12, 0.070, 0.030) * sunward * horizon;
    vec3 colour = base * 0.30 + iceHalo(ray, sun, 1.0, vec3(1.0, 0.88, 0.72), 0.0) * 1.6;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [0.998, 0.061, 0.0])
    renderer.full_screen()
    renderer.check('ice halo panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), '22-DEGREE ICE HALO / SUN DOGS / PILLAR / '
              'SYNTHETIC GPU PANORAMA (PREVIEW GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'ice-halos.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 3.5,
        'preview': 'Galaxy Shader/previews/ice-halos.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'ice-halo-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
