"""Report for the daytime star-field early-out (1.15.33).

The change is invisible, so this records the exact pixel differences between
the gated shader, the previous code and a star-free variant at noon and night,
plus the number of per-pixel star operations skipped in daylight.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_star_daytime import (W, H, VERTEX, gated_source, ungated_source,
                               starless_source)


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
        'starless': renderer.gl.compile(VERTEX, starless_source()),
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
        renderer.check('star daytime report')
        return renderer.read(W, H)[:, :, :3]

    day_gated = image(variants['gated'], 80.0)
    day_ungated = image(variants['ungated'], 80.0)
    day_starless = image(variants['starless'], 80.0)
    night_gated = image(variants['gated'], -25.0)
    night_ungated = image(variants['ungated'], -25.0)
    night_starless = image(variants['starless'], -25.0)

    for program in variants.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.33',
        'description': 'Skip the star cell hash, scintillation and colour '
                       'hashes when the remaining night sky is at most 0.002.',
        'renderer': f'{W}x{H} synthetic sky, float target',
        'per_pixel_work_skipped_in_daylight': [
            'star cell hash', 'two colour hashes', 'scintillation (3 sines)',
            'UV atan/asin and star mask'],
        'noon_gated_vs_previous_max_abs': float(np.abs(day_gated - day_ungated).max()),
        'noon_gated_vs_starless_max_abs': float(np.abs(day_gated - day_starless).max()),
        'night_gated_vs_previous_max_abs': float(np.abs(night_gated - night_ungated).max()),
        'night_star_energy_max_abs': float(np.abs(night_gated - night_starless).max()),
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'star-daytime-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
