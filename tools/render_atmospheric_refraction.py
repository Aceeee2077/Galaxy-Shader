"""Render a synthetic comparison of near-horizon atmospheric refraction.

Each panel shows the sun or full moon at 2 degrees elevation with the option
off (geometric disk) and on (lifted and vertically flattened). The background
is a synthetic gradient; this is not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 600, 300
HALF_X = 5.0
HALF_Y = 3.0
ELEVATION = 2.0
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
FRAME = '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform vec3 testCenter;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 center = normalize(testCenter);
    vec3 helper = abs(center.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(helper, center));
    vec3 up = cross(center, right);
    vec3 ray = normalize(center + right * tan(uv.x * radians(5.0)) +
                         up * tan(uv.y * radians(3.0)));
    vec3 colour;
'''


def sun_fragment(value):
    source = ('#version 330 compatibility\n#define DIMENSION 0\n' +
              expand(SHADERS / 'lib/common.glsl') +
              expand(SHADERS / 'lib/atmosphere.glsl') +
              FRAME + '''
    vec3 disk = atmosphere(ray, true) - atmosphere(ray, false);
    vec3 sky = mix(vec3(0.62, 0.34, 0.16), vec3(0.11, 0.17, 0.30),
                   smoothstep(-0.05, 0.10, ray.y));
    colour = sky + disk * 0.9;
    gl_FragColor = vec4(pow(colour / (colour + 0.9), vec3(1.0 / 2.2)), 1.0);
}''')
    return source.replace('#define ATMOSPHERIC_REFRACTION 1',
                          f'#define ATMOSPHERIC_REFRACTION {value}')


def moon_fragment(value):
    source = ('#version 330 compatibility\n#define DIMENSION 0\n' +
              expand(SHADERS / 'lib/common.glsl') +
              expand(SHADERS / 'lib/moon.glsl') +
              FRAME + '''
    vec3 sky = mix(vec3(0.035, 0.045, 0.075), vec3(0.008, 0.010, 0.020),
                   smoothstep(-0.02, 0.09, ray.y));
    colour = sky + moonSky(ray, 1.0, 0.0);
    gl_FragColor = vec4(pow(colour / (colour + 0.9), vec3(1.0 / 2.2)), 1.0);
}''')
    return source.replace('#define ATMOSPHERIC_REFRACTION 1',
                          f'#define ATMOSPHERIC_REFRACTION {value}')


def main():
    elevation = np.radians(ELEVATION)
    direction = np.array([np.cos(elevation), np.sin(elevation), 0.0], np.float32)
    renderer = Renderer(W, H)
    programs = {
        'sun_off': renderer.gl.compile(VERTEX, sun_fragment(0)),
        'sun_on': renderer.gl.compile(VERTEX, sun_fragment(1)),
        'moon_off': renderer.gl.compile(VERTEX, moon_fragment(0)),
        'moon_on': renderer.gl.compile(VERTEX, moon_fragment(1)),
    }

    def render(program):
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testSun', direction * 100.0)
        renderer.uniform(program, 'testCenter', direction * 100.0)
        renderer.uniform(program, 'sunPosition', direction * 100.0)
        renderer.uniform(program, 'moonPosition', direction * 100.0)
        renderer.uniform(program, 'moonPhase', 0)
        renderer.full_screen()
        renderer.check('atmospheric refraction preview')
        pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
        return Image.fromarray(pixels.astype(np.uint8))

    sun_off = render(programs['sun_off'])
    sun_on = render(programs['sun_on'])
    moon_off = render(programs['moon_off'])
    moon_on = render(programs['moon_on'])
    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    total_height = 26 + 18 + H + 18 + H
    preview = Image.new('RGB', (2 * W, total_height), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    draw.text((8, 7), 'ATMOSPHERIC REFRACTION / SUN AND FULL MOON AT 2 DEG '
              'ELEVATION / LEFT: GEOMETRIC DISK / RIGHT: LIFTED AND '
              'FLATTENED / SYNTHETIC GPU VIEW', fill=(225, 228, 235))
    draw.text((8, 30), 'SUN - LEFT: ATMOSPHERIC_REFRACTION=0   RIGHT: ON',
              fill=(190, 200, 215))
    preview.paste(sun_off, (0, 44))
    preview.paste(sun_on, (W, 44))
    draw.text((8, 44 + H + 4), 'MOON - LEFT: ATMOSPHERIC_REFRACTION=0   '
              'RIGHT: ON', fill=(190, 200, 215))
    preview.paste(moon_off, (0, 44 + H + 18))
    preview.paste(moon_on, (W, 44 + H + 18))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'atmospheric-refraction.png')

    report = {
        'type': 'Synthetic GPU disk comparison; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [2 * W, total_height],
        'panel_resolution': [W, H],
        'elevation_degrees': ELEVATION,
        'angular_window_degrees': [2.0 * HALF_X, 2.0 * HALF_Y],
        'panels': ['sun off', 'sun on', 'moon off', 'moon on'],
        'preview': 'Galaxy Shader/previews/atmospheric-refraction.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'atmospheric-refraction-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
