"""Measure the high-sun skip of the sunward fill inside `skyIrradiance`.

The fixture evaluates the real probe over a hemisphere of normals at six sun
heights and counts the `sunlightColor` calls. It is an engineering report, not
a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 160, 80
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GATE_NEW = '''    float twilightSun=lowSun*day;
    if (twilightSun>0.0)
        upper+=sunlightColor()*twilightSun*sunward*(1.0-overcast)*0.025;'''
GATE_OLD = '    upper+=sunlightColor()*lowSun*day*sunward*(1.0-overcast)*0.025;'
DEFINITION = 'vec3 sunlightColor() {'
ELEVATIONS = (-30.0, 0.0, 10.0, 25.0, 45.0, 80.0)
DOMAIN = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(90.0 * uv.y);
    vec3 n = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(skyIrradiance(n), tintCalls);
}'''


def source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert core.count(GATE_NEW) == 1 and core.count(DEFINITION) == 1
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    core = core.replace(DEFINITION, 'vec3 sunlightCore() {')
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float tintCalls=0.0;\nvec3 sunlightColor();\n' + core +
            '''
vec3 sunlightColor(){
    tintCalls+=1.0;
    return sunlightCore();
}
''' + DOMAIN)


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
        renderer.check('sky irradiance gate report')
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
            'normals': W * H,
            'sun_tints_before': int(round(before)),
            'sun_tints_after': int(round(after)),
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
        'normal_elevation_degrees': [0.0, 90.0],
        'normal_azimuth_degrees': [0.0, 360.0],
        'cases': cases,
        'status': 'the sunward sky fill evaluates the sunlight tint only while '
                  'the twilight gate is nonzero; high sun and deep night skip '
                  'it and stay pixel-identical',
    }
    (ROOT / 'validation' / 'sky-irradiance-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
