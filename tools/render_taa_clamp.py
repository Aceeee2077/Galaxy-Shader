"""Report for the five-tap low-profile TAA clamp (1.15.36).

The fixture places a distinct value only on the diagonal neighbours, so the
report shows the low profile ignoring them while quality 2 keeps the full box.
No preview is produced because quality 2 is unchanged and the low-profile
difference is a two-pixel clamp bound.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_taa_clamp import (W, H, VERTEX, UV, EDGE_VALUE, DIAGONAL_VALUE,
                            clamp_source, fixture_texture)


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    texture = fixture_texture(renderer)
    programs = {
        'low_0.1': renderer.gl.compile(VERTEX, clamp_source(1, '0.1')),
        'low_0.7': renderer.gl.compile(VERTEX, clamp_source(1, '0.7')),
        'quality2_0.1': renderer.gl.compile(VERTEX, clamp_source(2, '0.1')),
    }

    def image(program):
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'viewWidth', float(W))
        renderer.uniform(program, 'viewHeight', float(H))
        renderer.uniform(program, 'testUV', list(UV))
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, texture)
        renderer.uniform(program, 'colortex0', 0)
        renderer.full_screen()
        renderer.check('taa clamp report')
        return renderer.read(W, H)[:, :, :3]

    results = {name: float(image(program).mean())
               for name, program in programs.items()}
    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.36',
        'description': 'Use the centre plus four edge neighbours for the TAA '
                       'history clamp at TAA_QUALITY 1 instead of the 3x3 box.',
        'renderer': f'{W}x{H}, synthetic texture with {DIAGONAL_VALUE} on the '
                    f'four diagonals and {EDGE_VALUE} everywhere else',
        'texture_fetches_saved_per_low_profile_pixel': 4,
        'low_profile_history_0.1': results['low_0.1'],
        'low_profile_history_0.7': results['low_0.7'],
        'quality2_history_0.1': results['quality2_0.1'],
        'edge_value': EDGE_VALUE,
        'diagonal_value': DIAGONAL_VALUE,
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'taa-clamp-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
