"""Measure how many sky pixels skip the twilight-optics bodies.

The fixture samples `twilightOptics` directly. It is an engineering report,
not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U
from test_twilight_gate import BELT_GATE, ZODIAC_GATE, AIR_GATE, CLEAR_GATE

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
COUNTERS = ('float beltWork=0.0;\nfloat zodiacWork=0.0;\n'
            'float airWork=0.0;\n')


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            COUNTERS + expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/twilight_optics.glsl') +
            '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform float testOvercast;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(0.5 + 80.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = twilightOptics(ray, normalize(testSun), testOvercast);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def instrument(text):
    text = text.replace('    float arc = antiSolarArc(ray, sun);',
                        '    beltWork+=1.0;\n    float arc = antiSolarArc(ray, sun);')
    text = text.replace('    float cone = exp(',
                        '    zodiacWork+=1.0;\n    float cone = exp(')
    text = text.replace('    float layer = exp(',
                        '    airWork+=1.0;\n    float layer = exp(')
    return text


GATES = (BELT_GATE, ZODIAC_GATE, AIR_GATE, CLEAR_GATE)


def unpack(alpha):
    """Decode the belt/zodiac/air work counters packed into the alpha channel."""
    packed = np.rint(alpha.astype(np.float64))
    belt = np.rint(packed / 100.0)
    zodiac = np.rint((packed - 100.0 * belt) / 10.0)
    air = np.rint(packed - 100.0 * belt - 10.0 * zodiac)
    return int(belt.sum()), int(zodiac.sum()), int(air.sum())


def main():
    renderer = Renderer(W, H)
    probe = 'beltWork*100.0 + zodiacWork*10.0 + airWork'
    plain = source(probe)
    old_source = plain
    for gate in GATES:
        assert gate in old_source, gate
        old_source = old_source.replace(gate, '')
    programs = {
        'new': renderer.gl.compile(VERTEX, instrument(plain)),
        'old': renderer.gl.compile(VERTEX, instrument(old_source)),
    }

    def image(name, sun_deg, overcast):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'frameTimeCounter', 7.0)
        renderer.uniform(program, 'testOvercast', float(overcast))
        renderer.uniform(program, 'testSun',
                         [np.cos(np.deg2rad(sun_deg)),
                          np.sin(np.deg2rad(sun_deg)), 0.0])
        renderer.full_screen()
        renderer.check('twilight gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, sun, overcast in (('noon', 60.0, 0.0), ('low_day', 2.0, 0.0),
                                ('twilight', -10.0, 0.0),
                                ('deep_twilight', -35.0, 0.0),
                                ('night', -60.0, 0.0),
                                ('twilight_overcast', -10.0, 1.0)):
        new = image('new', sun, overcast)
        old = image('old', sun, overcast)
        before = unpack(old[:, :, 3])
        after = unpack(new[:, :, 3])
        cases[name] = {
            'sun_elevation_degrees': sun,
            'overcast': overcast,
            'bodies_entered_before': sum(before),
            'bodies_entered_after': sum(after),
            'belt_of_venus_entered': [before[0], after[0]],
            'zodiacal_light_entered': [before[1], after[1]],
            'airglow_entered': [before[2], after[2]],
            'share_skipping': round(1.0 - sum(after) / max(sum(before), 1), 4),
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
        'ray_field': {'azimuth': 'full circle', 'elevation_degrees': [0.5, 80.5]},
        'cases': cases,
        'status': 'the twilight bodies are pixel-identical and skipped '
                  'whenever their gate clamps to zero',
    }
    (ROOT / 'validation' / 'twilight-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
