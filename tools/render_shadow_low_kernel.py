"""Record the low shadow profile's four-tap kernel after removing rotation noise.

The fixture renders the real `shadowVisibility` at SHADOW_QUALITY 1 and counts
valueNoise calls. It is an engineering report, not a Minecraft screenshot.
"""
import json
import numpy as np
from build import ROOT, shader_digest
from test_shadow_low_kernel import ShadowLowKernel, shader_source


def main():
    ShadowLowKernel.setUpClass()
    try:
        data = ShadowLowKernel.image(ShadowLowKernel)
    finally:
        ShadowLowKernel.tearDownClass()
    visibility = data[:, :, 0]
    source = shader_source()
    start = source.index('#if SHADOW_QUALITY == 1')
    end = source.index('#else', start)
    low = source[start:end]
    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [32, 32],
        'profile': 'SHADOW_QUALITY=1',
        'value_noise_calls': float(data[:, :, 3].sum()),
        'visibility_min': float(visibility.min()),
        'visibility_max': float(visibility.max()),
        'visibility_mean': round(float(visibility.mean()), 6),
        'visibility_range': float(visibility.max() - visibility.min()),
        'status': 'the low profile uses a fixed four-tap cross with 2x2 jitter; '
                  'it no longer calls valueNoise or sin/cos for kernel rotation',
        'source_check': {
            'valueNoise_in_low_branch': 'valueNoise(' in low,
            'trig_in_low_branch': 'cos(' in low or 'sin(' in low,
        },
    }
    (ROOT / 'validation' / 'shadow-low-kernel-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
