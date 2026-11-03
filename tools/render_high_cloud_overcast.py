"""Report for the overcast early-out in the cirrus layer (1.15.37).

Records the layer output under full overcast and clear weather, and the noise
work skipped per overcast sky pixel. No preview is produced because the
overcast output is the input sky and clear weather is unchanged.
"""
import hashlib
import json

import numpy as np

from build import ROOT, SHADERS
from render_smoke import Renderer, U
from test_high_cloud_overcast import W, H, SKY, VERTEX, source


def shader_digest():
    digest = hashlib.sha256()
    for path in sorted(SHADERS.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(SHADERS).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    renderer = Renderer(W, H)
    program = renderer.gl.compile(VERTEX, source())

    def image(rain, thunder, wetness):
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'rainStrength', rain)
        renderer.uniform(program, 'thunderStrength', thunder)
        renderer.uniform(program, 'wetness', wetness)
        renderer.uniform(program, 'sunPosition', [0.0, 70.0, 71.0])
        renderer.uniform(program, 'moonPosition', [0.0, -70.0, -71.0])
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.uniform(program, 'frameCounter', 0)
        renderer.full_screen()
        renderer.check('high cloud overcast report')
        return renderer.read(W, H)[:, :, :3]

    overcast = image(1.0, 1.0, 1.0)
    clear = image(0.0, 0.0, 0.0)
    renderer.gl.delete_program(program)
    renderer.close()

    sky = np.broadcast_to(np.array(SKY, np.float32), (H, W, 3))
    report = {
        'version': '1.15.37',
        'description': 'Skip the cirrus warp and fbm when overcast fully hides '
                       'the layer; clear weather keeps the layer.',
        'renderer': f'{W}x{H}, fixed sky and ray',
        'per_pixel_noise_skipped_when_overcast': [
            'one valueNoise warp', 'one 2-4 octave fbm', 'one sine streak'],
        'overcast_output_vs_input_max_abs': float(np.abs(overcast - sky).max()),
        'clear_output_vs_input_max_abs': float(np.abs(clear - sky).max()),
        'shader_digest': shader_digest(),
    }
    out = ROOT / 'validation' / 'high-cloud-overcast-report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(out)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
