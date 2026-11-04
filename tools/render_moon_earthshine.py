"""Render a crescent moon with and without the phase-dependent earthshine.

The fixture calls `moonSky` directly against a dark night sky. The gain lifts
the earthshine into view, which clips the sunlit limb to white in both panels.
It is a synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 720, 300
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.8
PHASE = 3  # thin crescent: litFraction is about 0.15
PHASE_NEW = 'float earthshine = 0.45 + 1.10 * (1.0 - litFraction);'
PHASE_OLD = 'float earthshine = 1.0;'
FILL_NEW = 'vec3(0.028, 0.037, 0.058) * (1.0 - lit) * earthshine *'
FILL_OLD = 'vec3(0.010, 0.014, 0.022) * (1.0 - lit) * (0.4 + 0.6 * limb);'


def shader_source(old=False):
    core = (expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/atmospheric_refraction.glsl') +
            expand(SHADERS / 'lib/moon.glsl'))
    if old:
        core = core.replace(PHASE_NEW, PHASE_OLD)
        core = core.replace(FILL_NEW, FILL_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 moon = normalize(vec3(1.0, 0.0, 0.0));
    vec3 right = normalize(cross(moon, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, moon);
    float az = radians((uv.x - 0.5) * 9.0);
    float el = radians((uv.y - 0.5) * 9.0);
    vec3 ray = normalize(moon + right * tan(az) + up * tan(el));
    gl_FragColor = vec4(moonSky(ray, 1.0, 0.0), 1.0);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'with_earthshine': renderer.gl.compile(VERTEX, shader_source()),
        'previous': renderer.gl.compile(VERTEX, shader_source(old=True)),
    }

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'sunPosition', [300.0, 0.0, 0.0])
        renderer.uniform(program, 'moonPosition', [300.0, 0.0, 0.0])
        renderer.uniform(program, 'moonPhase', PHASE)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('moon earthshine preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('with_earthshine')
    old = image('previous')
    renderer.close()

    panels = []
    for label, data in (('PHASE-AWARE EARTHSHINE / CRESCENT MOON',
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
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'moon-earthshine.png')

    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'moon_phase': PHASE,
        'field_of_view_degrees': 9.0,
        'preview_gain': GAIN,
        'preview_note': 'gain clips the sunlit limb in both panels',
        'preview': 'Galaxy Shader/previews/moon-earthshine.png',
        'mean_luminance_previous': round(float(old.mean()), 6),
        'lit_fraction': round(0.5 + 0.5 * float(np.cos(np.pi * PHASE / 4.0)), 4),
        'mean_luminance_with_earthshine': round(float(new.mean()), 6),
        'mean_luminance_delta': round(float(new.mean() - old.mean()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'moon-earthshine-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
