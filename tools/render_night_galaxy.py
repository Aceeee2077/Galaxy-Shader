"""Render the rotating Milky Way sheet against the previous release.

Synthetic GPU sky fixtures only; these are not Minecraft screenshots. Both
variants use the same cameras, suns, clouds and post settings.
"""
import argparse
import json
import math
import zipfile
import numpy as np
from PIL import Image, ImageDraw
import render_smoke
from render_smoke import Renderer, look_at
from compare_performance import archive_source
from build import ROOT, shader_digest


TIMES = [('dusk', 1.09), ('evening', 1.30), ('midnight', 1.50), ('dawn', 1.91)]
AZIMUTHS = [('east', 0.0), ('south', math.pi / 2),
            ('west', math.pi), ('north', 3 * math.pi / 2)]
OPTIONS = {'TAA_QUALITY': 0, 'CLOUD_COVERAGE': 0.15}
ELEVATION = math.radians(34)


def sun_at(theta):
    # A small z component keeps the orthographic shadow camera's look_at
    # non-degenerate at midnight without changing the sky rotation.
    return np.array([math.cos(theta * math.pi), math.sin(theta * math.pi), 0.02],
                    dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='Galaxy Shader-1.14.1.zip')
    args = parser.parse_args()
    with zipfile.ZipFile(ROOT / args.baseline) as archive:
        before_source = archive_source(archive)
    current_source = render_smoke.source_for

    w, h = 480, 270
    renderer = Renderer(w, h)
    renderer.scene = lambda program, kind: None
    report = {'type': 'Synthetic GPU sky fixtures; not Minecraft screenshots',
              'baseline': args.baseline, 'shader_sha256': shader_digest(),
              'settings': dict(OPTIONS), 'scenarios': {}}
    rows = {'before': [], 'after': []}
    differences = []

    def render_variant(label, theta, variant, source):
        render_smoke.source_for = source
        renderer.programs = {}
        frames = []
        for az_label, azimuth in AZIMUTHS:
            direction = np.array([math.cos(azimuth) * math.cos(ELEVATION),
                                  math.sin(ELEVATION),
                                  math.sin(azimuth) * math.cos(ELEVATION)])
            renderer.rotation = look_at(np.zeros(3), direction)
            im, metrics = renderer.render('night', profile='HIGH', options=OPTIONS,
                                          sun_direction=sun_at(theta))
            frames.append(np.asarray(im))
            report['scenarios'][f'{variant}-{label}-{az_label}'] = metrics
        composition = Image.new('RGB', (w * len(frames), h))
        for i, data in enumerate(frames):
            composition.paste(Image.fromarray(data), (i * w, 0))
        return composition

    try:
        for label, theta in TIMES:
            for variant, source in [('before', before_source), ('after', current_source)]:
                rows[variant].append((label, render_variant(label, theta, variant, source)))
            differences.append(float(np.abs(
                np.asarray(rows['before'][-1][1], dtype=float) -
                np.asarray(rows['after'][-1][1], dtype=float)).mean()))
            print(label + ' rendered', flush=True)
    finally:
        render_smoke.source_for = current_source
        renderer.close()

    # Committed preview: only the current sheet, one row per phase of night.
    preview = Image.new('RGB', (w * len(AZIMUTHS), (h + 24) * len(rows['after'])),
                        (8, 10, 14))
    draw = ImageDraw.Draw(preview)
    for row, (label, composite) in enumerate(rows['after']):
        preview.paste(composite, (0, row * (h + 24) + 24))
        draw.text((8, row * (h + 24) + 6),
                  f'{label.upper()} / SYNTHETIC GPU SKY', fill=(225, 228, 235))
    preview.save(ROOT / 'Galaxy Shader' / 'previews' / 'night-galaxy.png')

    # Full A/B sheet stays a local validation artifact.
    comparison = Image.new('RGB', (w * len(AZIMUTHS), (h + 24) * len(rows['after']) * 2),
                           (8, 10, 14))
    draw = ImageDraw.Draw(comparison)
    for row, (label, composite) in enumerate(rows['after']):
        comparison.paste(composite, (0, row * (h + 24) + 24))
        draw.text((8, row * (h + 24) + 6),
                  f'AFTER / {label.upper()} / SYNTHETIC GPU SKY', fill=(225, 228, 235))
    for row, (label, composite) in enumerate(rows['before']):
        y = (len(rows['after']) + row) * (h + 24) + 24
        comparison.paste(composite, (0, y))
        draw.text((8, y - 18), f'BEFORE / {label.upper()} / SYNTHETIC GPU SKY',
                  fill=(225, 228, 235))
    comparison.save(ROOT / 'validation' / 'night-galaxy-comparison.png')

    report['checks'] = {
        'mean_abs_8bit_difference': float(np.mean(differences)),
        'preview': 'Galaxy Shader/previews/night-galaxy.png',
        'comparison': 'validation/night-galaxy-comparison.png',
    }
    report['status'] = 'rendered for visual review'
    (ROOT / 'validation' / 'night-galaxy-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['checks']), flush=True)


if __name__ == '__main__':
    main()
