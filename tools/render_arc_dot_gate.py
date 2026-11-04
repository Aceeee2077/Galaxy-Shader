"""Measure how many sky pixels skip the arc azimuth trigonometry.

The fixture samples `iceHaloCompanions` directly. It is an engineering report,
not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
CZA_GATE = 'azimuth > 0.48'
PARRY_GATE = 'azimuth > 0.865'
ALWAYS = 'azimuth > -2.0'
ARC_ACOS = 'acos(clamp(azimuth, -1.0, 1.0))'


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float arcCalls=0.0;\nfloat probeAcos(float x);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo_extras.glsl') +
            '''
float probeAcos(float x){arcCalls+=1.0;return acos(x);}
uniform vec2 testResolution;
uniform vec3 testSun;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(2.0 + 86.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = iceHaloCompanions(ray, normalize(testSun), 1.0);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def main():
    renderer = Renderer(W, H)
    base = source('arcCalls')
    old_source = base.replace(CZA_GATE, ALWAYS).replace(PARRY_GATE, ALWAYS)
    programs = {
        'new': renderer.gl.compile(VERTEX, base),
        'old': renderer.gl.compile(VERTEX, old_source),
        'new_probe': renderer.gl.compile(
            VERTEX, base.replace(ARC_ACOS,
                                 'probeAcos(clamp(azimuth, -1.0, 1.0))')),
        'old_probe': renderer.gl.compile(
            VERTEX, old_source.replace(
                ARC_ACOS, 'probeAcos(clamp(azimuth, -1.0, 1.0))')),
    }

    def image(name, sun_deg):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testSun',
                         [np.cos(np.deg2rad(sun_deg)),
                          np.sin(np.deg2rad(sun_deg)), 0.0])
        renderer.full_screen()
        renderer.check('arc dot gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for sun in (5.0, 20.0, 30.0, 70.0):
        new = image('new', sun)
        old = image('old', sun)
        new_calls = float(image('new_probe', sun)[:, :, 3].sum())
        old_calls = float(image('old_probe', sun)[:, :, 3].sum())
        cases[f'sun_{int(sun)}'] = {
            'pixels': W * H,
            'azimuth_trig_calls_before': old_calls,
            'azimuth_trig_calls_after': new_calls,
            'share_skipping': round((old_calls - new_calls) /
                                    max(old_calls, 1.0), 4),
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
        'ray_field': {'azimuth': 'full circle', 'elevation_degrees': [2.0, 88.0]},
        'cases': cases,
        'status': 'both azimuth dot gates are pixel-identical to the previous '
                  'arcs and skip their acos for most sky pixels',
    }
    (ROOT / 'validation' / 'arc-dot-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
