"""Render a synthetic lower-tangent-arc sky for visual review.

The fixture draws a high-sun daytime sky and samples the authored halo function
at a 40-degree sun. It is not a Minecraft screenshot.
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
    float az = radians(-45.0 + 90.0 * uv.x);
    float el = radians(2.0 + 63.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.42, 0.52, 0.70), vec3(0.12, 0.24, 0.52),
                   smoothstep(-0.02, 0.85, sin(el)));
    float disk = smoothstep(cos(radians(0.85)), cos(radians(0.60)),
                           dot(ray, sun));
    sky += vec3(1.0, 0.96, 0.86) * disk * 3.0;
    sky += vec3(0.24, 0.22, 0.17) * exp(-pow(acos(clamp(dot(ray, sun), -1.0, 1.0)) / 0.09, 2.0));
    vec3 halo = iceHalo(ray, sun, 1.0, vec3(1.0, 0.95, 0.88), 0.0);
    gl_FragColor = vec4(pow(max(sky + halo * 7.0, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    elevation = np.deg2rad(40.0)
    renderer.uniform(program, 'testSun',
                     [np.cos(elevation), np.sin(elevation), 0.0])
    renderer.full_screen()
    renderer.check('lower tangent arc panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'LOWER TANGENT ARC BELOW THE 22 DEG HALO / SUN AT 40 DEG / '
              'SYNTHETIC GPU PREVIEW (7x GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'lower-tangent-arc.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 40.0,
        'preview_gain': 7.0,
        'preview': 'Galaxy Shader/previews/lower-tangent-arc.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'lower-tangent-arc-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
