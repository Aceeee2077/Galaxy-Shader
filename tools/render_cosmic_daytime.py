"""Report for the daytime cosmic-sky early-out (1.15.32).

The change is invisible by construction, so no preview image is produced.
Instead the report records that the gated sky matches both the previous code
and a layer-free sky to the last bit at noon, and that the night and twilight
skies are unchanged, together with the count of noise layers that a daytime
sky pixel no longer evaluates.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_cosmic_daytime import (W, H, VERTEX, gated_source, ungated_source,
                                cosmic_off_source)


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    variants = {
        'gated': renderer.gl.compile(VERTEX, gated_source()),
        'ungated': renderer.gl.compile(VERTEX, ungated_source()),
        'cosmic_off': renderer.gl.compile(VERTEX, cosmic_off_source()),
    }

    def image(program, elevation_degrees):
        elevation = np.radians(elevation_degrees)
        sun = np.array([0.0, np.sin(elevation), np.cos(elevation)], np.float32)
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'sunPosition', sun * 100.0)
        renderer.uniform(program, 'moonPosition', -sun * 100.0)
        renderer.full_screen()
        renderer.check('cosmic daytime report')
        return renderer.read(W, H)[:, :, :3]

    day_gated = image(variants['gated'], 80.0)
    day_ungated = image(variants['ungated'], 80.0)
    day_off = image(variants['cosmic_off'], 80.0)
    night_gated = image(variants['gated'], -25.0)
    night_ungated = image(variants['ungated'], -25.0)
    night_off = image(variants['cosmic_off'], -25.0)
    dusk_gated = image(variants['gated'], -2.0)
    dusk_ungated = image(variants['ungated'], -2.0)

    for program in variants.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.32',
        'description': 'Skip the cosmic night-sky block when cosmicNight is '
                       'effectively zero, instead of evaluating galaxy, aurora, '
                       'meteor, comet and supernova noise before multiplying by zero.',
        'renderer': f'{W}x{H} synthetic sky, float target',
        'noise_layers_skipped_per_day_pixel': 6,
        'skipped_layers': ['galaxyNebula', 'auroraSky', 'auroraCorona',
                           'shootingStars (5 meteors)', 'cometSky (6 tail taps)',
                           'supernovaSky'],
        'noon_gated_vs_previous_max_abs': float(np.abs(day_gated - day_ungated).max()),
        'noon_gated_vs_cosmic_off_max_abs': float(np.abs(day_gated - day_off).max()),
        'night_gated_vs_previous_max_abs': float(np.abs(night_gated - night_ungated).max()),
        'night_cosmic_energy_max_abs': float(np.abs(night_gated - night_off).max()),
        'twilight_gated_vs_previous_max_abs': float(np.abs(dusk_gated - dusk_ungated).max()),
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'cosmic-daytime-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
