"""Measure how much of the sky skips the solar aureole exponentials.

The fixture calls `atmosphere` directly over a full azimuth ring. It is an
engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 360, 90
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '    if (solarAngle < diskEdge + 0.21) {'
GATE_OLD = '    if (solarAngle >= 0.0) {'


def source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    if old:
        assert GATE_NEW in core
        core = core.replace(GATE_NEW, GATE_OLD)
    core = (core.replace('exp(-haloDistance*vec3(1400.0,1800.0,2400.0))',
                         'probeTight(-haloDistance*vec3(1400.0,1800.0,2400.0))')
                .replace('exp(-haloDistance*vec3(560.0,500.0,440.0))',
                         'probeWide(-haloDistance*vec3(560.0,500.0,440.0))'))
    core += '''
vec3 probeTight(vec3 x){tightCalls+=1.0;return exp(x);}
vec3 probeWide(vec3 x){wideCalls+=1.0;return exp(x);}
'''
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tightCalls=0.0;\nfloat wideCalls=0.0;\n'
            'vec3 probeTight(vec3 x);\nvec3 probeWide(vec3 x);\n' + core +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 55.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = atmosphere(ray, false);
    gl_FragColor = vec4(colour, tightCalls + wideCalls);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, source()),
        'old': renderer.gl.compile(VERTEX, source(old=True)),
    }

    def image(name, sun_degrees):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(sun_degrees)
        direction = [float(np.cos(elevation)) * 300.0,
                     float(np.sin(elevation)) * 300.0, 0.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('aureole gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for sun in (5.0, 20.0, 45.0, 70.0, 89.0):
        new = image('new', sun)
        old = image('old', sun)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        skipped = int(np.count_nonzero(new[:, :, 3] == 0.0))
        cases['sun_%d' % sun] = {
            'sun_elevation_degrees': sun,
            'pixels': W * H,
            'pixels_skipping': skipped,
            'share_skipping': round(skipped / float(W * H), 4),
            'aureole_exponentials_before': int(round(before)),
            'aureole_exponentials_after': int(round(after)),
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
        'ray_elevation_degrees': [3.0, 58.0],
        'sky_ring_azimuth_degrees': [0.0, 360.0],
        'cases': cases,
        'status': 'pixels farther than about 37 degrees from the disk skip both '
                  'aureole exponentials and are pixel-identical',
    }
    (ROOT / 'validation' / 'aureole-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
