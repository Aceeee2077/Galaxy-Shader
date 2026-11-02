"""Render a synthetic close-up of the analytic green flash.

The fixture draws a simplified solar disk and samples the authored green-flash
function in a small angular window. It is not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/green_flash.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float dx = radians((uv.x * 2.0 - 1.0) * 6.0);
    float dy = radians((uv.y * 2.0 - 1.0) * 4.0);
    vec3 sun = normalize(testSun);
    vec3 helper = abs(sun.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(sun, helper));
    vec3 up = cross(right, sun);
    vec3 ray = normalize(sun + right * tan(dx) + up * tan(dy));
    float mu = dot(ray, sun);
    float edge = cos(radians(2.0));
    float disk = smoothstep(edge - 0.0004, edge + 0.0004, mu);
    float flashDim = 0.85 * greenFlashMask(ray, sun, 2.0);
    vec3 base = mix(vec3(0.030, 0.040, 0.085), vec3(0.24, 0.105, 0.035),
                    smoothstep(0.25, 1.0, 1.0 - clamp(length(vec2(dx, dy)) / 0.09, 0.0, 1.0)));
    vec3 colour = base + vec3(1.0, 0.42, 0.10) * disk * 2.4 * (1.0 - flashDim) +
                  greenFlash(ray, sun, 1.0, 2.0) * 1.3;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [np.cos(0.005), np.sin(0.005), 0.0])
    renderer.full_screen()
    renderer.check('green flash close-up')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'GREEN FLASH / SOLAR LIMB AT SUNSET / '
              'SYNTHETIC GPU CLOSE-UP (PREVIEW GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'green-flash.png')

    report = {
        'type': 'Synthetic GPU close-up; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_height': 0.005,
        'preview': 'Galaxy Shader/previews/green-flash.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'green-flash-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
