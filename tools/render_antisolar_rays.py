"""Render a synthetic anti-solar ray fan for visual review.

The fixture draws a simplified dusk gradient and samples the authored
anticrepuscular-ray function in a panorama centred on the anti-solar side. It is
not a Minecraft screenshot.
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
                expand(SHADERS / 'lib/antisolar_rays.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = radians(-90.0 + 180.0 * uv.x);
    float el = radians(-3.0 + 34.0 * uv.y);
    vec3 sun = normalize(testSun);
    vec3 anti = -sun;
    vec3 forward = normalize(vec3(anti.x, 0.0, anti.z));
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 ray = normalize(forward * cos(az) * cos(el) +
                         right * sin(az) * cos(el) +
                         vec3(0.0, 1.0, 0.0) * sin(el));
    vec3 horizon = vec3(0.235, 0.135, 0.095);
    vec3 zenith = vec3(0.030, 0.048, 0.092);
    vec3 sky = mix(horizon, zenith, smoothstep(-0.02, 0.45, sin(el)));
    float ground = smoothstep(0.012, -0.012, sin(el));
    sky = mix(sky, vec3(0.020, 0.023, 0.030), ground);
    vec3 rays = anticrepuscularRays(ray, sun, 0.0);
    gl_FragColor = vec4(pow(max(sky + rays * 7.0, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'testSun', [np.cos(0.02), np.sin(0.02), 0.0])
    renderer.full_screen()
    renderer.check('anti-solar rays panorama')
    pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
    renderer.gl.delete_program(program)
    renderer.close()

    image = Image.fromarray(pixels.astype(np.uint8))
    preview = Image.new('RGB', (W, H + 26), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'ANTICREPUSCULAR RAYS / ANTI-SOLAR PANORAMA / '
              'SYNTHETIC GPU PREVIEW (7x GAIN)', fill=(225, 228, 235))
    preview.paste(image, (0, 26))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'antisolar-rays.png')

    report = {
        'type': 'Synthetic GPU panorama; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': 1.15,
        'preview_gain': 7.0,
        'preview': 'Galaxy Shader/previews/antisolar-rays.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'antisolar-rays-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
