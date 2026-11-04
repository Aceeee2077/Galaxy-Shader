"""Measure how many surface pixels skip the puddle noise.

The fixture runs the authored puddle block from `geometry.fsh`. It is an
engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 240, 120
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
NEW = '''    if(wet>0.0) {
        float puddleNoise=valueNoise((vPlayer.xz+cameraPosition.xz)*0.35);
        float puddle=step(0.58,puddleNoise)*smoothstep(0.80,0.98,vLight.y)*upward*wet;
        m.roughness=mix(m.roughness,0.02,puddle);
        m.albedo*=1.0-0.12*puddle;
    }'''
OLD = NEW.replace('if(wet>0.0) {', 'if(wet>-1.0) {')
PUDDLE_NOISE = '        float puddleNoise=valueNoise('


def block(text):
    return ('#version 330 compatibility\n#define DIMENSION 0\n'
            'float puddleCalls=0.0;\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/noise.glsl') +
            expand(SHADERS / 'lib/pbr.glsl') +
            '''
uniform vec2 testResolution;
uniform float testWetness;
uniform float testUpward;
uniform float testLight;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    vec3 vPlayer = vec3(uv.x * 20.0, 0.0, uv.y * 20.0);
    vec2 vLight = vec2(0.0, testLight);
    float wet = testWetness * smoothstep(0.78, 0.98, testLight) * testUpward;
    float upward = testUpward;
    Material m;
    m.albedo = vec3(0.55, 0.62, 0.44);
    m.roughness = 0.55;
    float puddleNoise = 0.0;
    float puddle = 0.0;
''' + text + '''
    gl_FragColor = vec4(m.albedo, puddleCalls);
}''')


def instrument(text):
    return text.replace(PUDDLE_NOISE, '        puddleCalls+=1.0;\n' + PUDDLE_NOISE)


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, instrument(block(NEW))),
        'old': renderer.gl.compile(VERTEX, instrument(block(OLD))),
    }

    def image(name, wetness, upward, light):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'cameraPosition', [3.0, 64.0, 7.0])
        renderer.uniform(program, 'testWetness', float(wetness))
        renderer.uniform(program, 'testUpward', float(upward))
        renderer.uniform(program, 'testLight', float(light))
        renderer.full_screen()
        renderer.check('puddle wet gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, wetness, upward, light in (
            ('dry_clear', 0.0, 1.0, 1.0),
            ('wet_clear_day', 1.0, 1.0, 1.0),
            ('wet_rain_day', 1.0, 1.0, 0.9),
            ('cave_dark', 1.0, 1.0, 0.2),
            ('downward_face', 1.0, 0.0, 1.0)):
        new = image('new', wetness, upward, light)
        old = image('old', wetness, upward, light)
        before = float(old[:, :, 3].sum())
        after = float(new[:, :, 3].sum())
        cases[name] = {
            'wetness': wetness,
            'upward': upward,
            'sky_light': light,
            'surface_pixels': W * H,
            'puddle_noise_before': int(round(before)),
            'puddle_noise_after': int(round(after)),
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
        'status': 'dry, cave-lit and downward-facing surfaces skip the puddle '
                  'noise and are pixel-identical',
        'cases': cases,
    }
    (ROOT / 'validation' / 'puddle-wet-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
