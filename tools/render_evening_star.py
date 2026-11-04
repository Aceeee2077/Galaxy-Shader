"""Render the twilight sky with and without the evening star.

The fixture calls `atmosphere` over a western sky window with the sun nine
degrees below the horizon. It is a synthetic GPU preview, not a Minecraft
screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 720, 300
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.25
SUN_ELEVATION = -9.0
SUN_AZIMUTH = 2.4  # away from the aurora oval
GATE_NEW = '        if (venusWindow > 0.0) {'
GATE_OFF = '        if (venusWindow > 1.0) {'
SKY = '''
uniform float SUN_AZ;
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = SUN_AZ + radians((uv.x - 0.5) * 44.0);
    float el = radians(15.0 + 22.0 * uv.y);
    vec3 ray = normalize(vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az)));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}'''


def shader_source(venus=True):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert core.count(GATE_NEW) == 1
    if not venus:
        core = core.replace(GATE_NEW, GATE_OFF)
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + SKY


def main():
    renderer = Renderer(W, H)
    programs = {
        'with': renderer.gl.compile(VERTEX, shader_source()),
        'without': renderer.gl.compile(VERTEX, shader_source(venus=False)),
    }

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'SUN_AZ', float(SUN_AZIMUTH))
        angle = np.deg2rad(SUN_ELEVATION)
        direction = [float(np.cos(angle) * np.cos(SUN_AZIMUTH)) * 300.0,
                     float(np.sin(angle)) * 300.0,
                     float(np.cos(angle) * np.sin(SUN_AZIMUTH)) * 300.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('evening star preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('with')
    old = image('without')
    renderer.close()

    panels = []
    for label, data in (('WITH THE EVENING STAR / SUN AT -9 DEGREES', new),
                        ('PREVIOUS BEHAVIOUR', old)):
        pixels = np.clip(np.power(np.maximum(data, 0.0), 1.0 / 2.2) * GAIN
                         * 255.0, 0, 255)
        panel = Image.fromarray(pixels[::-1].astype(np.uint8))
        framed = Image.new('RGB', (W, H + 24), (7, 9, 13))
        ImageDraw.Draw(framed).text((8, 6), label, fill=(225, 228, 235))
        framed.paste(panel, (0, 24))
        panels.append(framed)
    preview = Image.new('RGB', (W, len(panels) * (H + 24)), (7, 9, 13))
    for index, panel in enumerate(panels):
        preview.paste(panel, (0, index * (H + 24)))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'evening-star.png')

    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': SUN_ELEVATION,
        'ray_elevation_degrees': [15.0, 37.0],
        'azimuth_window_degrees': 44.0,
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/evening-star.png',
        'peak_with_point': round(float(new.max()), 6),
        'peak_previous': round(float(old.max()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'evening-star-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
