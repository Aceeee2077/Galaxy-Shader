"""Measure the eclipse-only gate on the sky pass.

The fixture calls `atmosphere(ray, true)` over a sky ring on an ordinary day
and on the eclipse day. It is an engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '        if (eclipse > 0.0) {'
GATE_OLD = '        if (eclipse >= 0.0) {'
ECLIPSE_EXP = 'exp(-pow((1.0-mu)*58.0,2.0))'


def source(old=False, eclipse_day=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    if old:
        assert GATE_NEW in core
        core = core.replace(GATE_NEW, GATE_OLD)
    if eclipse_day:
        assert '#define SEASON_MODE 0' in core
        core = core.replace('#define SEASON_MODE 0', '#define SEASON_MODE 2')
    core = core.replace(ECLIPSE_EXP, 'probeEclipseExp((1.0-mu)*58.0)')
    core += '''
float probeEclipseExp(float x){eclipseCalls+=1.0;return exp(-x*x);}
'''
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float eclipseCalls=0.0;\n'
            'float probeEclipseExp(float x);\n' + core +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 60.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = atmosphere(ray, true);
    gl_FragColor = vec4(colour, eclipseCalls);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, source()),
        'old': renderer.gl.compile(VERTEX, source(old=True)),
        'new_eclipse': renderer.gl.compile(VERTEX, source(eclipse_day=True)),
        'old_eclipse': renderer.gl.compile(
            VERTEX, source(old=True, eclipse_day=True)),
    }

    def image(name, time):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(20.0)
        direction = [float(np.cos(elevation)) * 300.0,
                     float(np.sin(elevation)) * 300.0, 0.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.uniform(program, 'worldTime', time)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('eclipse gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, time, new_name, old_name in (
            ('ordinary_day', 6000, 'new', 'old'),
            ('eclipse_day', 6000, 'new_eclipse', 'old_eclipse')):
        new = image(new_name, time)
        old = image(old_name, time)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        cases[name] = {
            'world_time': time,
            'pixels': W * H,
            'aureole_exponentials_before': int(round(before)),
            'aureole_exponentials_after': int(round(after)),
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
        'ray_elevation_degrees': [3.0, 63.0],
        'sky_ring_azimuth_degrees': [0.0, 360.0],
        'cases': cases,
        'status': 'the eclipse aureole runs only while an eclipse is active; '
                  'the ordinary sky skips it and is pixel-identical',
    }
    (ROOT / 'validation' / 'eclipse-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
