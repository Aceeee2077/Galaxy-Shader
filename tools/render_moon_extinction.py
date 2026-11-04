"""Render a low moon with and without the atmospheric reddening.

The fixture calls `moonSky` directly against a dark night sky. It is a
synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 720, 300
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.0
ELEVATION = 3.0
TINT_NEW = 'vec3(1.00, 0.60, 0.36), vec3(1.0)'
TINT_OLD = 'vec3(1.0), vec3(1.0)'


def shader_source(old=False):
    core = (expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/atmospheric_refraction.glsl') +
            expand(SHADERS / 'lib/moon.glsl'))
    if old:
        core = core.replace(TINT_NEW, TINT_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
uniform float testElevation;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 moon = normalize(vec3(cos(radians(testElevation)),
                               sin(radians(testElevation)), 0.0));
    vec3 helper = abs(moon.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(moon, helper));
    vec3 up = cross(right, moon);
    float az = radians((uv.x - 0.5) * 26.0);
    float el = radians((uv.y - 0.5) * 26.0);
    vec3 ray = normalize(moon + right * tan(az) + up * tan(el));
    vec3 night = vec3(0.004, 0.006, 0.012) +
                 vec3(0.010, 0.012, 0.020) * smoothstep(0.0, 0.35, ray.y);
    gl_FragColor = vec4(night + moonSky(ray, 1.0, 0.0), 1.0);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'with_extinction': renderer.gl.compile(VERTEX, shader_source()),
        'previous': renderer.gl.compile(VERTEX, shader_source(old=True)),
    }

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testElevation', ELEVATION)
        renderer.uniform(program, 'sunPosition', [300.0, 0.0, 0.0])
        renderer.uniform(program, 'moonPosition',
                         [float(np.cos(np.deg2rad(ELEVATION))) * 300.0,
                          float(np.sin(np.deg2rad(ELEVATION))) * 300.0, 0.0])
        renderer.uniform(program, 'moonPhase', 0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('moon extinction preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('with_extinction')
    old = image('previous')
    renderer.close()

    panels = []
    for label, data in (('WITH ATMOSPHERIC EXTINCTION / MOON AT 3 DEG',
                         new),
                        ('PREVIOUS BEHAVIOUR', old)):
        pixels = np.clip(np.power(np.maximum(data, 0.0), 1.0 / 2.2) * GAIN
                         * 255.0, 0, 255)
        panel = Image.fromarray(pixels[::-1].astype(np.uint8))
        framed = Image.new('RGB', (W, H + 24), (7, 9, 13))
        ImageDraw.Draw(framed).text((8, 6), label, fill=(225, 228, 235))
        framed.paste(panel, (0, 24))
        panels.append(framed)
    preview = Image.new('RGB', (W, len(panels) * (H + 24)), (7, 9, 13))
    for index, panel in enumerate(panels):
        preview.paste(panel, (0, index * (H + 24)))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'moon-extinction.png')

    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'moon_elevation_degrees': ELEVATION,
        'field_of_view_degrees': 26.0,
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/moon-extinction.png',
        'mean_red_previous': round(float(old[:, :, 0].mean()), 6),
        'mean_red_with_extinction': round(float(new[:, :, 0].mean()), 6),
        'mean_blue_previous': round(float(old[:, :, 2].mean()), 6),
        'mean_blue_with_extinction': round(float(new[:, :, 2].mean()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'moon-extinction-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
