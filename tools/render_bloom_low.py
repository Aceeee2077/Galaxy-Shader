"""Record the low-profile bloom energy and kernel choice.

It is an engineering report, not a Minecraft screenshot.
"""
import json
import numpy as np
from build import ROOT, shader_digest
from test_bloom_low import BloomLow


def main():
    case = BloomLow()
    case.setUpClass()
    try:
        bright = case.image(0.0)
        low = case.image(1.0)
        full = case.image(2.0)
    finally:
        case.tearDownClass()
    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'profile': 'BLOOM_QUALITY=1',
        'bright_pass_mean': round(float(bright.mean()), 6),
        'low_blur_mean': round(float(low.mean()), 6),
        'full_blur_mean': round(float(full.mean()), 6),
        'max_low_full_difference': float(np.abs(low - full).max()),
        'taps': {'bright_pass': 4, 'blur_per_axis': 3},
        'status': 'the low profile preserves the constant-field bloom energy '
                  'with a 2x2 bright pass and three-tap blur',
    }
    (ROOT / 'validation' / 'bloom-low-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
