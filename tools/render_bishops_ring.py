"""Render a synthetic view of Bishop's ring around the sun.

The fixture builds rays over a wide sky patch centred on a synthetic sun and
brightens the dust aureole for review. It is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 1000, 620
GAIN = 8.0
FOV = 0.88
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/bishops_ring.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    uv.y *= testResolution.y / testResolution.x;
    vec3 sun = normalize(testSun);
    vec3 ref = abs(sun.y) < 0.95 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 east = normalize(cross(ref, sun));
    vec3 north = cross(sun, east);
    vec2 offset = uv * 0.88;
    float angle = length(offset);
    vec3 tangent = angle > 1e-5 ? normalize(east * offset.x + north * offset.y)
                                : east;
    vec3 ray = normalize(sun * cos(angle) + tangent * sin(angle));
    vec3 sky = mix(vec3(0.16, 0.32, 0.58), vec3(0.34, 0.52, 0.74),
                   smoothstep(0.0, 0.9, -uv.y));
    sky += vec3(1.0, 0.94, 0.82) * exp(-angle * 20.0) * 0.7;
    vec3 colour = sky + bishopsRing(ray, sun, 1.0, 0.0) * 8.0;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse',
                     np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [0.3, 0.5, 0.8])
    renderer.full_screen()
    renderer.check("Bishop's ring preview")
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), "BISHOP'S RING / BROAD VOLCANIC-DUST AUREOLE / WARM "
              'INNER EDGE, PALE BLUE OUTER SKIRT / SYNTHETIC GPU VIEW (GAIN)',
              fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'bishops-ring.png')

    report = {
        'type': 'Synthetic GPU sky patch; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'preview_gain': GAIN,
        'angular_window_degrees': 50.4,
        'preview': 'Galaxy Shader/previews/bishops-ring.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'bishops-ring-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
