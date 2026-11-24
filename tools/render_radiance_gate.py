"""Record how often a back-facing terrain fragment evaluates directional radiance.

The fixture calls the real `shadeSurface` with a call-counting probe. It is an
engineering report, not a Minecraft screenshot.
"""
import json
import numpy as np
from build import ROOT, shader_digest
from render_smoke import Renderer, U
from test_radiance_gate import H, VERTEX, W, shader_source

CASES = {
    'back_facing_lit': dict(sky=0.5, cloud=1.0),
    'back_facing_cloud_shade': dict(sky=0.5, cloud=0.6),
    'back_facing_foliage': dict(sky=0.5, cloud=1.0, ident=10001.0),
    'front_facing_lit': dict(sky=0.5, cloud=1.0, light=(0.0, 1.0, 0.0)),
}


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, shader_source()),
        'old': renderer.gl.compile(VERTEX, shader_source(old=True)),
    }
    dark = renderer.texture(1, 1, data=np.zeros((1, 1, 4), np.float32))

    def image(name, sky, cloud, ident=0.0, light=(0.0, 0.0, -1.0)):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        for uniform in ('gbufferModelView', 'gbufferModelViewInverse',
                        'shadowModelView'):
            renderer.uniform(program, uniform, np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'shadowProjection',
                         np.diag([0.05, 0.05, 0.05, 1.0]).astype(np.float32))
        renderer.uniform(program, 'shadowtex0', 0)
        renderer.uniform(program, 'eyeBrightnessSmooth', [0, 240])
        renderer.uniform(program, 'testNormal', [0.0, 1.0, 0.0])
        renderer.uniform(program, 'testSky', sky)
        renderer.uniform(program, 'testId', ident)
        renderer.uniform(program, 'testCloud', cloud)
        renderer.uniform(program, 'sunPosition', list(light))
        renderer.uniform(program, 'shadowLightPosition', list(light))
        renderer.uniform(program, 'moonPosition', [-v for v in light])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, dark)
        renderer.full_screen()
        renderer.check('radiance gate report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    report_cases = {}
    for name, args in CASES.items():
        new = image('new', **args)
        old = image('old', **args)
        report_cases[name] = {
            'radiance_calls_before': float(old[:, :, 3].sum()),
            'radiance_calls_after': float(new[:, :, 3].sum()),
            'calls_saved_per_pixel': round(
                float(old[:, :, 3].mean()) - float(new[:, :, 3].mean()), 4),
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
        'pixels': W * H,
        'cases': report_cases,
        'status': 'back-facing fully lit terrain now skips the atmospheric '
                  'transmittance chain; foliage, cloud shade and front-facing '
                  'terrain keep it',
    }
    (ROOT / 'validation' / 'radiance-gate-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report_cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
