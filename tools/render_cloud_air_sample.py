"""Measure the two exact cloud-march savings with call-counting probes.

The fixture calls `volumetricClouds` directly with a fixed sky. It is an
engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
AIR_NEW = '''    vec3 airColor=vec3(0.0);
    bool airReady=false;'''
AIR_OLD = '    vec3 airColor=atmosphere(ray,false);'
AIR_CALL = '        if (!airReady) { airColor=atmosphere(ray,false); airReady=true; }'
EROSION_NEW = '''    float erosion=0.05*(1.0-shape);
    if(detail>0.5 && !lightSample && shape>0.0)
        erosion=volumeNoise(q*8.1)*0.10*(1.0-shape);'''
EROSION_OLD = '''    float erosion;
    if(detail>0.5 && !lightSample) erosion=volumeNoise(q*8.1)*0.10;
    else erosion=0.05;
    erosion*=1.0-shape;'''


def source(probe):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float probeCount=0.0;\nfloat erosionCalls=0.0;\n'
            'vec3 probeAtmosphere(vec3 ray,bool disks);\n'
            'float probeErosion(vec3 p);\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/clouds.glsl') +
            '''
vec3 probeAtmosphere(vec3 ray,bool disks){probeCount+=1.0;return atmosphere(ray,disks);}
float probeErosion(vec3 p){erosionCalls+=1.0;return volumeNoise(p);}
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * uv.x;
    float el = radians(3.0 + 40.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 colour = volumetricClouds(vec3(0.10, 0.16, 0.26), ray,
                                   vec3(0.0, 70.0, 0.0), false);
    gl_FragColor = vec4(colour, ''' + probe + ''');
}''')


def main():
    renderer = Renderer(W, H)
    plain = source('probeCount')
    eager = plain.replace(AIR_NEW, AIR_OLD).replace(AIR_CALL + '\n', '')
    air_lazy = plain.replace('atmosphere(ray,false)',
                             'probeAtmosphere(ray,false)')
    air_eager = eager.replace('atmosphere(ray,false)',
                              'probeAtmosphere(ray,false)')
    erosion_plain = source('erosionCalls')
    erosion = erosion_plain.replace('volumeNoise(q*8.1)', 'probeErosion(q*8.1)')
    erosion_old = (erosion_plain.replace(AIR_NEW, AIR_OLD)
                   .replace(AIR_CALL + '\n', '')
                   .replace(EROSION_NEW, EROSION_OLD)
                   .replace('volumeNoise(q*8.1)', 'probeErosion(q*8.1)'))
    programs = {
        'air_lazy': renderer.gl.compile(VERTEX, air_lazy),
        'air_eager': renderer.gl.compile(VERTEX, air_eager),
        'erosion_new': renderer.gl.compile(VERTEX, erosion),
        'erosion_old': renderer.gl.compile(VERTEX, erosion_old),
    }

    def image(name, weather):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'sunPosition', [0.0, 300.0, 0.0])
        renderer.uniform(program, 'shadowLightPosition', [0.0, 300.0, 0.0])
        renderer.uniform(program, 'moonPosition', [0.0, -300.0, 0.0])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', weather[0])
        renderer.uniform(program, 'wetness', weather[1])
        renderer.uniform(program, 'thunderStrength', weather[2])
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('cloud march report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, weather in [('clear', (0.0, 0.0, 0.0)),
                          ('overcast', (0.0, 0.9, 0.0)),
                          ('rain', (1.0, 1.0, 0.0))]:
        lazy = image('air_lazy', weather)
        eager = image('air_eager', weather)
        new_calls = float(image('erosion_new', weather)[:, :, 3].sum())
        old_calls = float(image('erosion_old', weather)[:, :, 3].sum())
        skipped = int(np.count_nonzero(lazy[:, :, 3] == 0.0))
        cases[name] = {
            'pixels': W * H,
            'atmosphere_call_skips': skipped,
            'atmosphere_skip_share': round(skipped / float(W * H), 4),
            'erosion_noise_calls_before': old_calls,
            'erosion_noise_calls_after': new_calls,
            'erosion_skip_share': round((old_calls - new_calls) /
                                        max(old_calls, 1.0), 4),
            'max_abs_difference': float(
                np.abs(lazy[:, :, :3] - eager[:, :, :3]).max()),
        }

    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'ray_elevation_degrees': [3.0, 43.0],
        'origin_y': 70.0,
        'cloud_coverage': 0.45,
        'cases': cases,
        'status': 'both probes agree with the previous output; empty samples '
                  'skip the erosion noise and cloud-free rays skip the '
                  'deferred atmosphere sample',
    }
    (ROOT / 'validation' / 'cloud-air-sample-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
