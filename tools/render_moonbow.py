"""Render a synthetic panorama of the analytic lunar rainbow.

The fixture samples the authored moonbow function on an equirectangular dome
with a dim rainy-night gradient. It is not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/moonbow.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testMoon;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 0.60;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 moon = normalize(testMoon);
    float horizon = pow(1.0 - clamp(ray.y, 0.0, 1.0), 3.0);
    vec3 base = mix(vec3(0.005, 0.008, 0.017), vec3(0.030, 0.037, 0.052),
                    horizon);
    vec3 colour = base + moonbow(ray, moon, 1.0, 1.0, 1.0, 0.15) * 1.4;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    moon = [-np.cos(np.deg2rad(25.0)), np.sin(np.deg2rad(25.0)), 0.0]
    renderer.uniform(program, 'testMoon', moon)
    renderer.full_screen()
    renderer.check('moonbow panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'LUNAR RAINBOW / FULL MOON / RAIN / '
              'SYNTHETIC GPU PANORAMA (PREVIEW GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'moonbow.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'moon_elevation_degrees': 25.0,
        'moon_phase': 0,
        'preview': 'Galaxy Shader/previews/moonbow.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'moonbow-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
