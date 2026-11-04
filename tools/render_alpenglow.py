"""Render the cloud deck at twilight with and without the alpenglow term.

The fixture draws the authored atmosphere and cloud march for a sun ten degrees
below the horizon. It is a synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 240
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 0.9
GATE_NEW = '''    float alpenglowGate = smoothstep(-0.30, -0.13, sun.y) *
                          (1.0 - smoothstep(-0.02, 0.07, sun.y));'''
GATE_OLD = '    float alpenglowGate = -1.0;'
SUN_HEIGHT = -0.18


def source():
    return ('#version 330 compatibility\n#define DIMENSION 0\n' +
            expand(SHADERS / 'lib/common.glsl') +
            expand(SHADERS / 'lib/clouds.glsl') +
            '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float az = 6.2831853 * (uv.x - 0.5);
    float el = radians(3.0 + 40.0 * uv.y);
    vec3 ray = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
    vec3 sky = atmosphere(ray, false);
    gl_FragColor = vec4(volumetricClouds(sky, ray, vec3(0.0, 70.0, 0.0),
                                         false), 1.0);
}''')


def main():
    renderer = Renderer(W, H)
    base = source()
    programs = {
        'with_alpenglow': renderer.gl.compile(VERTEX, base),
        'previous': renderer.gl.compile(VERTEX, base.replace(GATE_NEW, GATE_OLD)),
    }
    elevation = float(np.arcsin(SUN_HEIGHT))
    direction = [float(np.cos(elevation)), SUN_HEIGHT, 0.0]

    def image(name):
        program = programs[name]
        renderer.bind_fbo([renderer.final])
        renderer.call('glUseProgram', None, [U], program)
        renderer.uniform(program, 'gbufferModelViewInverse',
                         np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'sunPosition',
                         [component * 300.0 for component in direction])
        renderer.uniform(program, 'shadowLightPosition',
                         [component * 300.0 for component in direction])
        renderer.uniform(program, 'moonPosition',
                         [-component * 300.0 for component in direction])
        renderer.uniform(program, 'worldTime', 6000)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        renderer.uniform(program, 'frameTimeCounter', 0.0)
        renderer.full_screen()
        renderer.check('alpenglow preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('with_alpenglow')
    old = image('previous')
    delta = new - old
    renderer.close()

    panels = []
    for label, data in (('WITH ALPENGLOW / SUN 10 DEG BELOW THE HORIZON',
                         new),
                        ('PREVIOUS BEHAVIOUR', old)):
        pixels = np.clip((np.power(np.maximum(data, 0.0), 1.0 / 2.2) * GAIN)
                         * 255.0, 0, 255)
        panel = Image.fromarray(pixels[::-1].astype(np.uint8))
        framed = Image.new('RGB', (W, H + 24), (7, 9, 13))
        ImageDraw.Draw(framed).text((8, 6), label, fill=(225, 228, 235))
        framed.paste(panel, (0, 24))
        panels.append(framed)
    preview = Image.new('RGB', (W, len(panels) * (H + 24)), (7, 9, 13))
    for index, panel in enumerate(panels):
        preview.paste(panel, (0, index * (H + 24)))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'alpenglow.png')

    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'sun_height': SUN_HEIGHT,
        'sun_elevation_degrees': round(float(np.degrees(elevation)), 2),
        'ray_elevation_degrees': [3.0, 43.0],
        'origin_y': 70.0,
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/alpenglow.png',
        'mean_luminance_previous': round(float(old.mean()), 6),
        'mean_luminance_with_alpenglow': round(float(new.mean()), 6),
        'mean_added_red': round(float(delta[:, :, 0].mean()), 6),
        'mean_added_green': round(float(delta[:, :, 1].mean()), 6),
        'mean_added_blue': round(float(delta[:, :, 2].mean()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'alpenglow-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
