"""Render the synthetic solar eclipse corona for visual review.

The fixture draws a dark eclipse sky and samples the authored corona around a
black lunar disk. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 620
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/eclipse_corona.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testTime;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-18.0 + 36.0 * uv.x);
    float el = radians(27.0 + 36.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sun = normalize(testSun);
    float angle = acos(clamp(dot(ray, sun), -1.0, 1.0));
    vec3 sky = mix(vec3(0.012, 0.020, 0.040), vec3(0.004, 0.008, 0.018),
                   smoothstep(0.20, 0.75, sin(el)));
    float moonDisk = 1.0 - smoothstep(cos(radians(0.60)),
                                     cos(radians(0.51)), angle);
    vec3 colour = sky * (1.0 - moonDisk);
    colour += eclipseCorona(ray, sun, 1.0, testTime) * 3.0;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    sun = np.array([np.cos(0.785), np.sin(0.785), 0.0])
    renderer.uniform(program, 'testSun', sun.tolist())
    renderer.uniform(program, 'testTime', 12.0)
    renderer.full_screen()
    renderer.check('eclipse corona preview')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'TOTAL SOLAR ECLIPSE / CORONA STREAMERS AND RED '
              'PROMINENCES / SYNTHETIC GPU PREVIEW (3x GAIN)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'eclipse-corona.png')

    report = {
        'type': 'Synthetic GPU eclipse view; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_gain': 3.0,
        'preview': 'Galaxy Shader/previews/eclipse-corona.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'eclipse-corona-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
