"""Render the northern twilight sky with and without the aurora gate.

The fixture calls `atmosphere` with the sun just below the horizon, where the
dome is still bright and the curtains used to appear at full strength. It is a
synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 720, 300
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.1
SUN_ELEVATION = -6.0
GATE_NEW = '            float auroraNight = 1.0-smoothstep(-0.20,-0.05,sun.y);'
GATE_OLD = '            float auroraNight = 1.0;'
SKY = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = -1.5707963 + radians((uv.x - 0.5) * 70.0);
    float el = radians(2.0 + 30.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    gl_FragColor = vec4(atmosphere(ray, true), 1.0);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/atmosphere.glsl')
    assert GATE_NEW in core
    if old:
        core = core.replace(GATE_NEW, GATE_OLD)
    return '#version 330 compatibility\n#define DIMENSION 0\n' + core + SKY


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, shader_source()),
        'old': renderer.gl.compile(VERTEX, shader_source(old=True)),
    }

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        angle = np.deg2rad(SUN_ELEVATION)
        direction = [float(np.cos(angle)) * 300.0, float(np.sin(angle)) * 300.0, 0.0]
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
        renderer.check('aurora twilight preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('new')
    old = image('old')
    renderer.close()

    panels = []
    for label, data in (('AURORA FADING OUT OF TWILIGHT / SUN AT -6 DEGREES', new),
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
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'aurora-twilight.png')

    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_elevation_degrees': SUN_ELEVATION,
        'ray_elevation_degrees': [2.0, 32.0],
        'azimuth_window_degrees': 70.0,
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/aurora-twilight.png',
        'green_previous': round(float(old[:, :, 1].mean()), 6),
        'green_with_fade': round(float(new[:, :, 1].mean()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'aurora-twilight-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
