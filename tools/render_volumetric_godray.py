"""Report for the zero-strength god-ray early-out (1.15.34).

Records that the gated shader matches the previous code at strength 0 and 1,
that a clear sky costs exactly zero when shafts are disabled, and that the
storm flash still survives. No preview is produced because the change is
invisible.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_volumetric_godray import (W, H, VERTEX, light_source, with_strength,
                                    ungated)


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    base = light_source()
    programs = {
        'on0': renderer.gl.compile(VERTEX, with_strength(base, '0.0')),
        'on1': renderer.gl.compile(VERTEX, with_strength(base, '1.0')),
        'old0': renderer.gl.compile(VERTEX, ungated(with_strength(base, '0.0'))),
        'old1': renderer.gl.compile(VERTEX, ungated(with_strength(base, '1.0'))),
    }
    ones = np.ones((4, 4, 4), np.float32)
    shadow = renderer.texture(4, 4, data=ones)

    def image(program, player=(0.0, 4.0, 2.0), rain=0.0, thunder=0.0,
              flash=0.0, water=0):
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'testPlayer', list(player))
        renderer.uniform(program, 'shadowProjection', np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'shadowModelView', np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'shadowDistance', 100.0)
        renderer.uniform(program, 'shadowMapResolution', 2048)
        renderer.uniform(program, 'sunPosition', [0.0, 34.2, 94.0])
        renderer.uniform(program, 'moonPosition', [0.0, -34.2, -94.0])
        renderer.uniform(program, 'cameraPosition', [0.0, 70.0, 0.0])
        renderer.uniform(program, 'rainStrength', rain)
        renderer.uniform(program, 'thunderStrength', thunder)
        renderer.uniform(program, 'lightningBoltPosition',
                         [0.0, 0.0, 0.0, flash])
        renderer.uniform(program, 'eyeBrightnessSmooth', [220, 220])
        renderer.uniform(program, 'isEyeInWater', int(water))
        renderer.uniform(program, 'frameCounter', 0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, shadow)
        renderer.uniform(program, 'shadowtex0', 0)
        renderer.full_screen()
        renderer.check('volumetric god-ray report')
        return renderer.read(W, H)[:, :, :3]

    on1 = image(programs['on1'])
    old1 = image(programs['old1'])
    on0 = image(programs['on0'], rain=0.7, thunder=0.8, flash=1.0)
    old0 = image(programs['old0'], rain=0.7, thunder=0.8, flash=1.0)
    clear = image(programs['on0'])
    storm = image(programs['on0'], rain=1.0, thunder=1.0, flash=1.0)
    underwater = image(programs['on0'], player=(0.0, 1.0, 2.0), water=1)

    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.34',
        'description': 'Skip the shadowed volumetric shaft integral when '
                       'GODRAY_STRENGTH is zero, keeping only the lightning flash.',
        'renderer': f'{W}x{H}, one sample per pixel',
        'shadow_taps_skipped_at_quality_2': {'zenith': 8, 'horizon': 16},
        'enabled_vs_previous_max_abs': float(np.abs(on1 - old1).max()),
        'disabled_vs_previous_max_abs': float(np.abs(on0 - old0).max()),
        'disabled_clear_max_abs': float(np.abs(clear).max()),
        'disabled_storm_max': float(storm.max()),
        'disabled_storm_blue_green_ratio': float(storm[..., 2].max() /
                                                 max(storm[..., 1].max(), 1e-9)),
        'disabled_underwater_max_abs': float(np.abs(underwater).max()),
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'volumetric-godray-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
