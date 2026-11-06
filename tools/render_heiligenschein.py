"""Render a dewy grass patch with and without the heiligenschein.

The fixture casts camera rays at a ground plane from eye height with the sun
low behind the observer, so the antisolar point sits near the centre. It is a
synthetic GPU preview, not a Minecraft screenshot.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 640, 360
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
GAIN = 1.0
SUN_ELEVATION = 10.0
WORLD_TIME = 1000
BLOCK_NEW = '''    if (foliage > 0.5) {
        float clock = float(worldTime % 24000);
        float dew = 1.0 - smoothstep(2000.0, 4600.0, clock);
        // A narrow backscatter lobe, about ten degrees wide at half height.
        // Six squarings keep it to multiplies on the low-end paths.
        float s = sat(dot(v, light));
        float s2 = s * s;
        float s4 = s2 * s2;
        float s8 = s4 * s4;
        float s16 = s8 * s8;
        float retro = s16 * s16 * s16; // s^48
        direct += m.albedo * sunRadiance * retro * dew * shadow *
                  (0.35 + 0.65 * nl) * 0.45 *
                  (1.0 - 0.70 * weatherRainAmount());
    }
'''
GROUND = '''
uniform vec2 testResolution;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float aspect = testResolution.x / testResolution.y;
    vec3 forward = normalize(vec3(-cos(radians(12.0)), -sin(radians(12.0)), 0.0));
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, forward);
    vec2 ndc = (uv - 0.5) * vec2(aspect, 1.0) * 2.0;
    vec3 dir = normalize(forward + right * ndc.x * tan(radians(32.0)) +
                         up * ndc.y * tan(radians(32.0)));
    if (dir.y > -0.01) {
        gl_FragColor = vec4(vec3(0.020, 0.026, 0.034), 1.0);
        return;
    }
    vec3 player = dir * (-1.6 / dir.y);
    vec3 n = normalize(vec3(sin(player.x * 7.0) * 0.10 +
                            sin(player.z * 13.0) * 0.06,
                            1.0,
                            cos(player.z * 9.0) * 0.10 +
                            sin(player.x * 23.0) * 0.04));
    Material m = defaultMaterial(vec3(0.18, 0.32, 0.14), n);
    vec3 colour = shadeSurface(m, player, vec2(0.0, 1.0), 10001.0);
    gl_FragColor = vec4(colour, 1.0);
}'''


def shader_source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/lighting.glsl')
    assert core.count(BLOCK_NEW) == 1
    if old:
        core = core.replace(BLOCK_NEW, '')
    return ('#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'
            + core + GROUND).replace('#define CLOUD_QUALITY 3',
                                     '#define CLOUD_QUALITY 0')


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
        for uniform in ('gbufferModelView', 'gbufferModelViewInverse',
                        'shadowModelView'):
            renderer.uniform(program, uniform, np.eye(4, dtype=np.float32))
        renderer.uniform(program, 'shadowProjection',
                         np.diag([0.05, 0.05, 0.05, 1.0]).astype(np.float32))
        renderer.uniform(program, 'shadowtex0', 0)
        renderer.uniform(program, 'eyeBrightnessSmooth', [0, 240])
        renderer.uniform(program, 'testResolution', [W, H])
        renderer.uniform(program, 'worldTime', WORLD_TIME)
        renderer.uniform(program, 'worldDay', 60)
        renderer.uniform(program, 'rainStrength', 0.0)
        renderer.uniform(program, 'wetness', 0.0)
        renderer.uniform(program, 'thunderStrength', 0.0)
        angle = np.deg2rad(SUN_ELEVATION)
        direction = [float(np.cos(angle)) * 300.0,
                     float(np.sin(angle)) * 300.0, 0.0]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1, renderer.white)
        renderer.full_screen()
        renderer.check('heiligenschein preview')
        data = renderer.read(W, H)[:, :, :3]
        assert np.isfinite(data).all()
        return data

    new = image('new')
    old = image('old')
    renderer.close()

    panels = []
    for label, data in (('DEWY MORNING GRASS / SUN 10 DEGREES BEHIND THE OBSERVER', new),
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
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'heiligenschein.png')

    added = np.maximum(new - old, 0.0)
    report = {
        'type': 'Synthetic GPU preview; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'world_time': WORLD_TIME,
        'sun_elevation_degrees': SUN_ELEVATION,
        'preview_gain': GAIN,
        'preview': 'Galaxy Shader/previews/heiligenschein.png',
        'mean_green_previous': round(float(old[:, :, 1].mean()), 6),
        'mean_green_with_glow': round(float(new[:, :, 1].mean()), 6),
        'peak_added_green': round(float(added[:, :, 1].max()), 6),
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'heiligenschein-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
