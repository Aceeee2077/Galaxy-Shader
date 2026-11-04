"""Measure how many halo-cap pixels skip the lunar companions.

The fixture samples `iceHalo` inside the 37-degree cap. It is an engineering
report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
LUNAR_GATE = 'if (pillarGate > 0.0 || lunarDogGate > 0.0) {'
ALWAYS = 'if (pillarGate > -1.0) {'
HALO_ATAN = 'atan(dot('


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float haloAtan=0.0;\nfloat probeAtan(float y, float x);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/ice_halo.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testVisibility;
uniform float testLunar;
float probeAtan(float y, float x){haloAtan+=1.0;return atan(y,x);}
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 light = normalize(testSun);
    vec3 up = abs(light.y) > 0.95 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 u = normalize(cross(up, light));
    vec3 w = cross(light, u);
    float theta = radians(35.5 * uv.y);
    float phi = 6.2831853 * uv.x;
    vec3 ray = normalize(cos(theta) * light +
                         sin(theta) * (cos(phi) * u + sin(phi) * w));
    vec3 colour = iceHalo(ray, light, testVisibility, vec3(1.0),
                          testLunar);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def main():
    renderer = Renderer(W, H)
    base = source('haloAtan')
    old_source = base.replace(LUNAR_GATE, ALWAYS)
    programs = {
        'new': renderer.gl.compile(VERTEX, base.replace(HALO_ATAN,
                                                        'probeAtan(dot(')),
        'old': renderer.gl.compile(VERTEX, old_source.replace(
            HALO_ATAN, 'probeAtan(dot(')),
    }

    def image(name, sun_deg, lunar):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testVisibility', 1.0)
        renderer.uniform(program, 'testLunar', float(lunar))
        renderer.uniform(program, 'testSun',
                         [np.cos(np.deg2rad(sun_deg)) * np.cos(0.6),
                          np.sin(np.deg2rad(sun_deg)),
                          np.cos(np.deg2rad(sun_deg)) * np.sin(0.6)])
        renderer.full_screen()
        renderer.check('lunar companion gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, sun, lunar in (('moon_3', 3.0, 1.0), ('moon_10', 10.0, 1.0),
                             ('moon_20', 20.0, 1.0), ('moon_24', 24.0, 1.0),
                             ('moon_30', 30.0, 1.0), ('moon_50', 50.0, 1.0),
                             ('moon_70', 70.0, 1.0), ('sun_10', 10.0, 0.0),
                             ('sun_50', 50.0, 0.0)):
        new = image('new', sun, lunar)
        old = image('old', sun, lunar)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        cases[name] = {
            'light_elevation_degrees': sun,
            'lunar': bool(lunar),
            'halo_cap_pixels': W * H,
            'trig_calls_before': int(round(before)),
            'trig_calls_after': int(round(after)),
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
        'ray_field': {'polar_angle_degrees': [0.0, 35.5],
                      'azimuth': 'full circle around the light'},
        'cases': cases,
        'status': 'the lunar halo companions are pixel-identical and skip '
                  'their moon basis and atan whenever both gates are zero',
    }
    (ROOT / 'validation' / 'lunar-companion-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
