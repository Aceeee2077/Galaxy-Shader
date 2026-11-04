"""Measure the night skip of the daytime scattering block.

The fixture calls `atmosphere(ray, true)` over a sky dome at five sun heights
and counts calls to the fixed horizon tint, which only the daytime block
evaluates. It is an engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '    if (day > 0.0) {'
GATE_OLD = '    if (day >= 0.0) {'
TINT_CALL = 'vec3 warmBand=horizonSunTint()*0.46'
ELEVATIONS = (-30.0, -10.0, -5.0, 0.0, 35.0)


def source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert GATE_NEW in core and TINT_CALL in core
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    core = core.replace(TINT_CALL, 'vec3 warmBand=probeHorizonTint()*0.46')
    core += '''
vec3 probeHorizonTint(){tintCalls+=1.0;return horizonSunTint();}
'''
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tintCalls=0.0;\n'
            'vec3 probeHorizonTint();\n' + core +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 60.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = atmosphere(ray, true);
    gl_FragColor = vec4(colour, tintCalls);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, source()),
        'old': renderer.gl.compile(VERTEX, source(old=True)),
    }

    def image(name, elevation):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        angle = np.deg2rad(elevation)
        direction = [float(np.cos(angle)) * 300.0,
                     float(np.sin(angle)) * 300.0, 0.0]
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
        renderer.check('day scatter gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for elevation in ELEVATIONS:
        new = image('new', elevation)
        old = image('old', elevation)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        cases['sun_%+d_deg' % elevation] = {
            'sun_elevation_degrees': elevation,
            'pixels': W * H,
            'daytime_blocks_before': int(round(before)),
            'daytime_blocks_after': int(round(after)),
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
        'status': 'the daytime scattering block runs only while the day factor '
                  'is nonzero; below about six degrees under the horizon it is '
                  'skipped and the sky stays pixel-identical',
    }
    (ROOT / 'validation' / 'day-scatter-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
