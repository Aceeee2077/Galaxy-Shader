"""Record the medium cloud self-shadow budget and before/after error.

It is an engineering report, not a Minecraft screenshot.
"""
import json
import numpy as np
from build import ROOT, shader_digest
from test_cloud_low_shadow import CloudLowShadow


def main():
    CloudLowShadow.setUpClass()
    try:
        rows = {}
        for height in (210.0, 230.0, 260.0, 300.0):
            new = CloudLowShadow.sample(CloudLowShadow.new, height)
            old = CloudLowShadow.sample(CloudLowShadow.old, height)
            rows[str(int(height))] = {
                'calls_before': float(old[:, :, 3].sum()),
                'calls_after': float(new[:, :, 3].sum()),
                'shadow_before': round(float(old[:, :, 0].mean()), 6),
                'shadow_after': round(float(new[:, :, 0].mean()), 6),
                'max_abs_difference': float(np.abs(new[:, :, 0] - old[:, :, 0]).max()),
            }
    finally:
        CloudLowShadow.tearDownClass()
    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'profile': 'CLOUD_QUALITY=2',
        'cases': rows,
        'status': 'the medium profile evaluates one longer cloud light sample '
                  'instead of two short ones while keeping the broad shadow',
    }
    (ROOT / 'validation' / 'cloud-low-shadow-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
