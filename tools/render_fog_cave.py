"""Report for the enclosed-space fog early-out (1.15.39).

The change is invisible, so this records the fog output with and without the
gate for cave, indoor and outdoor light levels. No preview is produced.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_fog_cave import W, H, VERTEX, GATED, UNGATED, fog_source


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    source = fog_source()
    new = renderer.gl.compile(VERTEX, source)
    old = renderer.gl.compile(VERTEX, source.replace(GATED, UNGATED))

    def image(program, player, sky_light, sky=0):
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testPlayer', list(player))
        renderer.uniform(program, 'testColor', 0.5)
        renderer.uniform(program, 'testSky', sky)
        renderer.uniform(program, 'eyeBrightnessSmooth', [0, sky_light])
        renderer.uniform(program, 'sunPosition', [80.0, 2.0, 60.0])
        renderer.uniform(program, 'moonPosition', [-80.0, -2.0, -60.0])
        renderer.uniform(program, 'cameraPosition', [0.0, 70.0, 0.0])
        renderer.uniform(program, 'isEyeInWater', 0)
        renderer.uniform(program, 'far', 1024.0)
        renderer.full_screen()
        renderer.check('fog cave report')
        return renderer.read(W, H)[:, :, :3]

    cases = {
        'cave_sky_light_0': (((170.0, 170.0, 0.0), 0)),
        'indoor_sky_light_0': (((-170.0, 170.0, 0.0), 0)),
        'dusk_sky_light_60': (((170.0, 170.0, 0.0), 60)),
        'day_sky_light_240': (((170.0, 170.0, 0.0), 240)),
        'sky_flag_day': (((170.0, 170.0, 0.0), 240, 1)),
    }
    results = {}
    for name, args in cases.items():
        a = image(new, *args)
        b = image(old, *args)
        results[name] = {
            'gated_mean': float(a.mean()),
            'previous_mean': float(b.mean()),
            'max_abs_difference': float(np.abs(a - b).max()),
        }

    for program in (new, old):
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.39',
        'description': 'Skip the full atmosphere sample in terrain fog when the '
                       'pixel has no outdoor sky light (cave or interior) or '
                       'when the sky flag already zeroes the fog.',
        'renderer': f'{W}x{H}, constant 0.5 input colour',
        'sky_evaluations_skipped': 'one full atmosphere() call per covered '
                                   'pixel in caves and interiors, and per sky '
                                   'pixel',
        'cases': results,
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'fog-cave-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
