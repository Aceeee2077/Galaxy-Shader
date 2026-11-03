"""Report for the zero-strength bloom early-out (1.15.35).

The passes are invisible on their own, so this records their output with and
without a bright HDR input at strength 0 and 1. No preview is produced.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from validate import source_for
from render_smoke import Renderer, U
from test_bloom_strength import W, H, VERTEX


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    programs = {}
    for name in ('composite1', 'composite2', 'composite3'):
        for strength in ('0.0', '1.0'):
            programs[(name, strength)] = renderer.gl.compile(
                VERTEX, source_for(SHADERS / 'program' / f'{name}.fsh',
                                   {'BLOOM_STRENGTH': strength}))
    bright = renderer.texture(4, 4, data=np.full((4, 4, 4), 4.0, np.float32))

    def image(name, strength, sampler):
        program = programs[(name, strength)]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'viewWidth', float(W))
        renderer.uniform(program, 'viewHeight', float(H))
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, bright)
        renderer.uniform(program, sampler, 0)
        renderer.full_screen()
        renderer.check('bloom strength report')
        return renderer.read(W, H)[:, :, :3]

    results = {}
    for name, sampler in (('composite1', 'colortex0'),
                          ('composite2', 'colortex5'),
                          ('composite3', 'colortex6')):
        results[name] = {
            'strength_0_max': float(np.abs(image(name, '0.0', sampler)).max()),
            'strength_1_mean': float(image(name, '1.0', sampler).mean()),
            'strength_1_max': float(image(name, '1.0', sampler).max()),
        }

    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'version': '1.15.35',
        'description': 'Skip the bloom bright pass and both blur passes when '
                       'BLOOM_STRENGTH is zero, plus the composite4 fetch.',
        'renderer': f'{W}x{H}, constant HDR 4.0 input',
        'texture_fetches_skipped_at_zero': {
            'composite1_bright_pass': 16,
            'composite2_horizontal_blur': 5,
            'composite3_vertical_blur': 5,
            'composite4_fetch': 1,
            'total': 27,
        },
        'passes': results,
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'bloom-strength-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
