"""Render a low star field with and without the atmospheric extinction.

The fixture calls `atmosphere` directly over a night-sky window. It is a
synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 700, 420
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.5
PEDESTAL = 0.0
LOSS_GAIN = 2000.0
STAR_NEW = ('vec3 starExtinction = mix(vec3(0.78,0.52,0.34), vec3(1.0),\n'
            '                                      smoothstep(0.10,0.44,ray.y));')
STAR_OLD = 'vec3 starExtinction = vec3(1.0);'


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert STAR_NEW in core
    if old:
        core = core.replace(STAR_NEW, STAR_OLD)
    return ('#version 330 compatibility\n#define DIMENSION 0\n' + core + '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 1.2 + 0.733 * uv.x;
    float el = radians(4.0 + 24.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}''')


def main():
    renderer = Renderer(W, H)
    programs = {
        'with_extinction': renderer.gl.compile(VERTEX, shader_source()),
        'previous': renderer.gl.compile(VERTEX, shader_source(old=True)),
    }

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        elevation = np.deg2rad(-30.0)
        direction = [float(np.cos(elevation)) * 300.0,
                     float(np.sin(elevation)) * 300.0, 0.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.uniform(program, 'worldTime', 18000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('star extinction preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('with_extinction')
    old = image('previous')
    renderer.close()

    lost = np.maximum(old - new, 0.0) * LOSS_GAIN
    panels = []
    for label, pixels in (
            ('STELLAR EXTINCTION NEAR THE HORIZON', None),
            ('PREVIOUS BEHAVIOUR', None),
            ('LIGHT LOST TO EXTINCTION, AMPLIFIED x%d' % LOSS_GAIN, lost)):
        if pixels is None:
            data = new if label.startswith('STELLAR') else old
            lifted = np.maximum(data - PEDESTAL, 0.0)
            pixels = np.clip(np.power(lifted, 1.0 / 2.2) * GAIN * 255.0, 0, 255)
        else:
            pixels = np.clip(pixels * 255.0, 0, 255)
        panel = Image.fromarray(pixels[::-1].astype(np.uint8))
        framed = Image.new('RGB', (W, H + 24), (7, 9, 13))
        ImageDraw.Draw(framed).text((8, 6), label, fill=(225, 228, 235))
        framed.paste(panel, (0, 24))
        panels.append(framed)
    preview = Image.new('RGB', (W, len(panels) * (H + 24)), (7, 9, 13))
    for index, panel in enumerate(panels):
        preview.paste(panel, (0, index * (H + 24)))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'star-extinction.png')

    elevation = 4.0 + 24.0 * (np.arange(H) + 0.5) / H
    rows = (elevation >= 4.0) & (elevation <= 12.0)
    band_new = new[rows]
    band_old = old[rows]
    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'ray_elevation_degrees': [4.0, 28.0],
        'sky_ring_azimuth_radians': [1.2, 1.933],
        'measured_band_degrees': [4.0, 12.0],
        'preview_gain': GAIN,
        'loss_amplification': LOSS_GAIN,
        'preview_pedestal': PEDESTAL,
        'preview': 'Galaxy Shader/previews/star-extinction.png',
        'red_loss': round(float((band_old[:, :, 0] - band_new[:, :, 0]).sum()), 6),
        'green_loss': round(float((band_old[:, :, 1] - band_new[:, :, 1]).sum()), 6),
        'blue_loss': round(float((band_old[:, :, 2] - band_new[:, :, 2]).sum()), 6),
        'stars_affected': int((np.abs(new - old).max(axis=2) > 0.0).sum()),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'star-extinction-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
