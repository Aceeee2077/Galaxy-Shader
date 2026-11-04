"""Measure how many sky pixels skip the parhelic band exponential.

The fixture samples `iceHaloCompanions` over the upper sky. It is an
engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE = 'if (sun.y > 0.02 && abs(ray.y - sun.y) < 0.15) {'
OLD_GATE = 'if (sun.y > 0.02) {'
BAND_EXP = '        float height = exp(-pow((ray.y - sun.y) / 0.009, 2.0));'


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float parhelicExp=0.0;\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo_extras.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(1.0 + 84.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = iceHaloCompanions(ray, normalize(testSun), testVisibility);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def instrument(text):
    return text.replace(BAND_EXP,
                        '        parhelicExp+=1.0;\n' + BAND_EXP)


def main():
    renderer = Renderer(W, H)
    base = instrument(source('parhelicExp'))
    old_source = base.replace(GATE, OLD_GATE)
    programs = {
        'new': renderer.gl.compile(VERTEX, base),
        'old': renderer.gl.compile(VERTEX, old_source),
    }

    def image(name, sun_deg):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testVisibility', 1.0)
        renderer.uniform(program, 'testSun',
                         [np.cos(np.deg2rad(sun_deg)),
                          np.sin(np.deg2rad(sun_deg)), 0.0])
        renderer.full_screen()
        renderer.check('parhelic gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, sun in (('sun_5', 5.0), ('sun_20', 20.0), ('sun_40', 40.0),
                      ('sun_60', 60.0), ('sun_89', 89.0)):
        new = image('new', sun)
        old = image('old', sun)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        cases[name] = {
            'sun_elevation_degrees': sun,
            'sky_pixels': W * H,
            'band_exp_before': int(round(before)),
            'band_exp_after': int(round(after)),
            'share_skipping': round(1.0 - after / max(before, 1.0), 4),
            'max_abs_difference': float(
                np.abs(new[:, :, :3] - old[:, :, :3]).max()),
        }

    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'ray_field': {'azimuth': 'full circle', 'elevation_degrees': [1.0, 85.0]},
        'cases': cases,
        'status': 'the parhelic circle is pixel-identical and skips its band '
                  'exponential outside a 0.15-radian window around sun height',
    }
    (ROOT / 'validation' / 'parhelic-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
