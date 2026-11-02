"""Render a synthetic double rainbow for visual review.

The fixture draws a simplified rain sky, a primary bow matching the atmosphere
term, the authored secondary bow and Alexander's dark band. It is not a
Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 480
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/secondary_rainbow.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float el = uv.y * 1.05;
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    vec3 sky = mix(vec3(0.20, 0.24, 0.30), vec3(0.075, 0.105, 0.16),
                   smoothstep(0.0, 0.55, sin(el)));
    float angle = acos(clamp(dot(ray, -sun), -1.0, 1.0));
    float spectral = (angle - 0.655) / 0.145;
    vec3 primary = vec3(0.0);
    if (spectral > 0.0 && spectral < 1.0) {
        float edge = smoothstep(0.0, 0.09, spectral) *
                     (1.0 - smoothstep(0.91, 1.0, spectral));
        primary = mix(vec3(0.40, 0.16, 0.74), vec3(0.10, 0.32, 0.95),
                      smoothstep(0.06, 0.24, spectral));
        primary = mix(primary, vec3(0.06, 0.80, 0.40),
                      smoothstep(0.23, 0.46, spectral));
        primary = mix(primary, vec3(0.98, 0.86, 0.12),
                      smoothstep(0.46, 0.68, spectral));
        primary = mix(primary, vec3(1.0, 0.22, 0.07),
                      smoothstep(0.68, 0.94, spectral));
        primary *= edge * 0.62;
    }
    float alexander = smoothstep(0.72, 0.76, angle) *
                      (1.0 - smoothstep(0.83, 0.87, angle));
    sky *= 1.0 - 0.08 * alexander;
    vec3 secondary = secondaryRainbow(ray, sun, 1.0, 0.0, 1.0) * 1.6;
    gl_FragColor = vec4(pow(max(sky + primary + secondary, 0.0),
                            vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [-np.cos(0.436), np.sin(0.436), 0.0])
    renderer.full_screen()
    renderer.check('double rainbow panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'DOUBLE RAINBOW / SUN AT 25 DEG BEHIND CAMERA / '
              'SYNTHETIC GPU PREVIEW (SECONDARY 1.6x)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'secondary-rainbow.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 25.0,
        'preview_gain': 'secondary 1.6x',
        'preview': 'Galaxy Shader/previews/secondary-rainbow.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'secondary-rainbow-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
