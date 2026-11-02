"""Render a synthetic auroral zenith corona for visual review.

The fixture looks up into a dark sky and draws the authored converging rays.
It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 640, 640
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/aurora_corona.glsl') +
                '''
uniform vec2 testResolution;
void main() {
    vec2 p = (gl_FragCoord.xy - 0.5 * testResolution) /
             min(testResolution.x, testResolution.y) * 2.0;
    float r = length(p);
    float az = atan(p.y, p.x);
    float theta = min(r, 1.0) * 0.96; // 55 degrees from the zenith
    vec3 ray = vec3(sin(theta) * cos(az), cos(theta), sin(theta) * sin(az));
    vec3 sky = mix(vec3(0.008, 0.024, 0.028), vec3(0.002, 0.006, 0.012),
                   smoothstep(0.10, 1.0, r));
    vec3 corona = auroraCorona(ray, 1.0, 7.0) * 4.0;
    if (r > 1.0) sky = vec3(0.0);
    gl_FragColor = vec4(pow(max(sky + corona, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.full_screen()
    renderer.check('aurora corona preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'AURORA ZENITH CORONA / FISHEYE TO 55 DEG / '
              'SYNTHETIC GPU PREVIEW (CORONA 4x)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'aurora-corona.png')

    report = {
        'type': 'Synthetic GPU upper-sky panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'view_zenith_angle_degrees': 55.0,
        'preview_gain': 'corona 4x',
        'preview': 'Galaxy Shader/previews/aurora-corona.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'aurora-corona-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
