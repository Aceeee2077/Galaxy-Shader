"""Record numeric reference defaults without importing reference shader code."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from build import ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    selected={
        'SUN_I','SUN_NR','SUN_NG','SUN_NB','SUN_MR','SUN_MG','SUN_MB',
        'SUN_ER','SUN_EG','SUN_EB','SUN_ANGULAR_RADIUS','MOON_ANGULAR_RADIUS',
        'MOON_R','MOON_G','MOON_B','SKYLIGHT_I','CLOUD_SHADOWS_INTENSITY',
        'SHADOW_PENUMBRA_SCALE','AUTO_EXPOSURE','GRADE_WHITE_BALANCE',
        'GRADE_SATURATION','GRADE_CONTRAST','AIR_FOG_RAYLEIGH_DENSITY',
        'AIR_FOG_MIE_DENSITY_MORNING','AIR_FOG_MIE_DENSITY_NOON',
        'AIR_FOG_MIE_DENSITY_EVENING','AIR_FOG_MIE_FALLOFF_START',
        'AIR_FOG_MIE_FALLOFF_HALF_LIFE',
    }
    with ZipFile(args.archive) as archive:
        settings=archive.read('shaders/settings.glsl').decode('utf-8')
    definitions=dict(re.findall(r'^[ \t]*#define[ \t]+(\w+)[ \t]+([^\s/]+)',settings,re.M))
    values={key:definitions[key] for key in sorted(selected)}
    assert values['SUN_ANGULAR_RADIUS']=='2.0'
    assert values['CLOUD_SHADOWS_INTENSITY']=='0.80'
    assert values['AUTO_EXPOSURE']=='AUTO_EXPOSURE_OFF'
    report={
        'reference_archive':args.archive.name,
        'reference_archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'reference_source':'shaders/settings.glsl',
        'defaults':values,
        'scope':'Numeric reference only. No reference shaders or LUT assets are bundled.',
        'mapping':{
            'SUN_ANGULAR_RADIUS':'2 degrees; shared Galaxy disk and PCSS radius',
            'CLOUD_SHADOWS_INTENSITY':'Galaxy CLOUD_SHADOW_STRENGTH=0.8',
            'AUTO_EXPOSURE':'Galaxy AUTO_EXPOSURE=0, EXPOSURE=1.0',
            'AIR_FOG_MIE_FALLOFF_START':'69 blocks absolute = sea level 62 + 7',
            'AIR_FOG_MIE_FALLOFF_HALF_LIFE':'7 blocks, applied only to the new low mist term',
            'sun_color':'Independent relative optical-path approximation, calibrated in Galaxy HDR units',
        },
    }
    output=ROOT/'validation/photon-parameters.json'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
