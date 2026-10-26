"""Render the analytic moon phase sheet and a synthetic night context.

The phase row samples moonSky() directly at a 3 degree half-FOV; the wide frame
runs the full shader pipeline. Both are synthetic GPU fixtures, not Minecraft
screenshots.
"""
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, look_at, U

PHASES = ['FULL', 'WANING GIBBOUS', 'LAST QUARTER', 'WANING CRESCENT',
          'NEW', 'WAXING CRESCENT', 'FIRST QUARTER', 'WAXING GIBBOUS']
CELL = 160
CONTEXT_W, CONTEXT_H = 1280, 480
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'


def phase_strip():
    renderer = Renderer(CELL, CELL)
    fragment = ('#version 330 compatibility\n#define DIMENSION 0\n' +
                expand(SHADERS / 'lib/common.glsl') +
                expand(SHADERS / 'lib/moon.glsl') +
                '''
uniform vec2 testResolution;
uniform vec3 testCenter;
uniform float testNight;
uniform float testOvercast;
void main() {
    vec2 p = gl_FragCoord.xy / testResolution * 2.0 - 1.0;
    vec3 center = normalize(testCenter);
    vec3 helper = abs(center.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(center, helper));
    vec3 up = cross(right, center);
    vec3 ray = normalize(center + right * p.x * tan(radians(3.0)) +
                         up * p.y * tan(radians(3.0)));
    vec3 sky = moonSky(ray, testNight, testOvercast);
    gl_FragColor = vec4(sky + vec3(0.003, 0.004, 0.008), 1.0);
}''')
    program = renderer.gl.compile(VERTEX, fragment)
    renderer.bind_fbo([renderer.final])
    renderer.call('glUseProgram', None, [U], program)
    renderer.uniform(program, 'gbufferModelViewInverse', np.eye(4, dtype=np.float32))
    renderer.uniform(program, 'testResolution', [CELL, CELL])
    renderer.uniform(program, 'testCenter', [0.0, 1.0, 0.0])
    renderer.uniform(program, 'testNight', 1.0)
    renderer.uniform(program, 'testOvercast', 0.0)
    renderer.uniform(program, 'moonPosition', [0.0, 100.0, 0.0])
    renderer.uniform(program, 'sunPosition', [0.0, -100.0, 0.0])
    renderer.uniform(program, 'shadowLightPosition', [0.0, -100.0, 0.0])
    cells = []
    try:
        for phase in range(8):
            renderer.uniform(program, 'moonPhase', phase)
            renderer.full_screen()
            renderer.check(f'moon phase {phase}')
            data = renderer.read(CELL, CELL)[::-1, :, :3]
            cells.append(Image.fromarray(np.uint8(np.clip(data, 0.0, 1.0) * 255)))
    finally:
        renderer.gl.delete_program(program)
        renderer.close()
    return cells


def context_frame():
    elevation = math.radians(34)
    moon = np.array([0.0, math.sin(elevation), math.cos(elevation)], dtype=np.float32)
    renderer = Renderer(CONTEXT_W, CONTEXT_H)
    renderer.scene = lambda program, kind: None
    renderer.rotation = look_at(np.zeros(3), moon)
    try:
        image, metrics = renderer.render(
            'night', profile='HIGH',
            options={'TAA_QUALITY': 0, 'CLOUD_COVERAGE': 0.15},
            sun_direction=-moon, moon_phase=0)
    finally:
        renderer.close()
    return image, metrics, moon


def main():
    cells = phase_strip()
    context, metrics, moon = context_frame()

    header = 26
    label_row = 22
    width = max(CONTEXT_W, CELL * len(PHASES))
    sheet = Image.new('RGB', (width, header + CONTEXT_H + label_row + CELL), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 7), 'FULL MOON / SYNTHETIC GPU SKY (NOT A MINECRAFT SCREENSHOT)',
              fill=(225, 228, 235))
    sheet.paste(context, (0, header))
    draw.text((8, header + CONTEXT_H + 5), 'MOON PHASES 0-7 / SYNTHETIC GPU SKY',
              fill=(225, 228, 235))
    y = header + CONTEXT_H + label_row
    for i, cell in enumerate(cells):
        sheet.paste(cell, (i * CELL, y))
        draw.text((i * CELL + 4, y + CELL - 14), PHASES[i], fill=(190, 198, 212))
    sheet.save(ROOT / 'Galaxy Shader' / 'previews' / 'night-moon.png')

    report = {
        'type': 'Synthetic GPU sky fixtures; not Minecraft screenshots',
        'shader_sha256': shader_digest(),
        'moon_direction': [float(v) for v in moon],
        'phase_order': PHASES,
        'context_draw': metrics,
        'preview': 'Galaxy Shader/previews/night-moon.png',
        'status': 'rendered for visual review',
    }
    (ROOT / 'validation' / 'night-moon-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'preview': report['preview'], 'mean': metrics['mean']}), flush=True)


if __name__ == '__main__':
    main()
