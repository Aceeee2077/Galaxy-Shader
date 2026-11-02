"""Render synthetic panoramas of the twilight and airglow optics.

These fixtures sample the authored sky functions on an equirectangular dome and
add a neutral background gradient so the new structure is legible. They are not
Minecraft screenshots and do not represent final exposure or terrain.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 960, 240
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
SCENES = [
    ('dusk', -0.06, 0.0, 6.0),
    ('midnight', -0.80, 1.0, 14.0),
]


def main():
    renderer = Renderer(W, H)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/twilight_optics.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testSun;
uniform int testScene;
uniform float testGain;
void main() {
    vec2 uv = gl_FragCoord.xy / testResolution;
    float azimuth = (uv.x * 2.0 - 1.0) * 3.14159265359;
    float elevation = uv.y * 1.20;
    vec3 ray = vec3(cos(elevation) * cos(azimuth), sin(elevation),
                    cos(elevation) * sin(azimuth));
    vec3 sun = normalize(testSun);
    float horizon = pow(1.0 - clamp(ray.y, 0.0, 1.0), 3.0);
    vec3 base = mix(vec3(0.010, 0.016, 0.028), vec3(0.022, 0.032, 0.052), horizon);
    if (testScene < 0.5) {
        base *= 1.0 - 0.35 * earthShadowMask(ray, sun);
    }
    // The preview boosts the authored optics against a dim base so the
    // structure is legible; final in-game exposure is much lower.
    vec3 colour = base * 0.30 + twilightOptics(ray, sun, 0.0) * testGain;
    gl_FragColor = vec4(pow(max(colour, 0.0), vec3(1.0 / 2.2)), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [W, H])
    renderer.uniform(program, 'frameTimeCounter', 60.0)

    rows = []
    for label, sun_height, scene, gain in SCENES:
        horizontal = np.sqrt(max(0.0, 1.0 - sun_height * sun_height))
        renderer.uniform(program, 'testSun', [horizontal, sun_height, 0.0])
        renderer.uniform(program, 'testScene', int(scene))
        renderer.uniform(program, 'testGain', gain)
        renderer.full_screen()
        renderer.check(label)
        pixels = np.clip(renderer.read(W, H)[::-1, :, :3] * 255.0, 0, 255)
        rows.append((label, pixels.astype(np.uint8)))
        print(label + ' rendered', flush=True)
    renderer.gl.delete_program(program)
    renderer.close()

    title = 26
    preview = Image.new('RGB', (W, (H + title) * len(rows)), (7, 9, 13))
    draw = ImageDraw.Draw(preview)
    for index, (label, data) in enumerate(rows):
        y = index * (H + title)
        note = ('DUSK / ANTI-SOLAR SHADOW + BELT (LEFT/RIGHT EDGES), '
                'ZODIACAL CONE (CENTRE)' if label == 'dusk'
                else 'MIDNIGHT / UPPER-ATMOSPHERE AIRGLOW')
        draw.text((8, y + 7), note + ' / SYNTHETIC GPU SKY', fill=(225, 228, 235))
        preview.paste(Image.fromarray(data), (0, y + title))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'twilight-optics.png')

    report = {
        'type': 'Synthetic GPU panoramas; not Minecraft screenshots',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'scenes': [
            {'label': label, 'sun_height': sun_height, 'gain': gain}
            for label, sun_height, _, gain in SCENES
        ],
        'preview': 'Galaxy Shader/previews/twilight-optics.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'twilight-optics-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview']}), flush=True)


if __name__ == '__main__':
    main()
