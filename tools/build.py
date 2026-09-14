"""Generate Iris entrypoints/settings and a deterministic, directly installable ZIP."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'Galaxy Shader'
SHADERS = PACK / 'shaders'
VERSION = '1.5.0'

PROGRAMS = {
    'gbuffers_basic': ('geometry', 'effect', ['BASIC']),
    'gbuffers_line': ('geometry', 'effect', ['BASIC']),
    'gbuffers_textured': ('geometry', 'geometry', []),
    'gbuffers_textured_lit': ('geometry', 'geometry', []),
    'gbuffers_terrain': ('geometry', 'geometry', ['TERRAIN']),
    'gbuffers_damagedblock': ('geometry', 'effect', ['TERRAIN']),
    'gbuffers_entities': ('geometry', 'geometry', ['ENTITY']),
    'gbuffers_entities_translucent': ('geometry', 'translucent', ['ENTITY']),
    'gbuffers_entities_glowing': ('geometry', 'geometry', ['ENTITY']),
    'gbuffers_spidereyes': ('geometry', 'effect', ['ENTITY']),
    'gbuffers_block': ('geometry', 'geometry', ['BLOCK_ENTITY']),
    'gbuffers_block_translucent': ('geometry', 'translucent', ['BLOCK_ENTITY']),
    'gbuffers_hand': ('geometry', 'geometry', ['HAND']),
    'gbuffers_hand_water': ('geometry', 'geometry', ['HAND']),
    'gbuffers_water': ('geometry', 'translucent', ['TERRAIN']),
    'gbuffers_weather': ('geometry', 'weather', []),
    'gbuffers_particles': ('geometry', 'translucent', []),
    'gbuffers_particles_translucent': ('geometry', 'translucent', []),
    'gbuffers_armor_glint': ('geometry', 'effect', []),
    'gbuffers_beaconbeam': ('geometry', 'effect', []),
    'gbuffers_lightning': ('geometry', 'effect', ['BASIC']),
    'gbuffers_skybasic': ('fullscreen', 'sky', []),
    'gbuffers_skytextured': ('fullscreen', 'sky', []),
    'gbuffers_clouds': ('fullscreen', 'sky', []),
    'shadow': ('shadow', 'shadow', []),
    **{name: ('fullscreen', name, []) for name in
       ['deferred', 'composite', 'composite1', 'composite2', 'composite3', 'composite4', 'final']},
}

PROFILE_KEYS = ['shadowMapResolution','shadowDistance','SHADOW_QUALITY','TAA_QUALITY','CLOUD_QUALITY',
                'WATER_QUALITY','SSR_QUALITY','AO_QUALITY','INDIRECT_QUALITY',
                'VOLUMETRIC_QUALITY','WEATHER_QUALITY','TERRAIN_FOG_QUALITY',
                'BLOOM_QUALITY','DOF_QUALITY','MOTION_BLUR']
PROFILES = {
    'POTATO': [1024,'64.0',1,0,1,1,0,0,0,0,0,0,1,0,0],
    'LOW': [1024,'96.0',1,1,1,1,0,1,0,0,1,1,1,0,0],
    'MEDIUM': [2048,'96.0',2,2,2,2,1,1,0,1,2,1,2,0,0],
    'HIGH': [2048,'128.0',3,3,3,2,2,2,1,2,3,2,2,0,0],
    'ULTRA': [4096,'192.0',4,3,4,3,3,3,2,3,4,3,3,0,0],
    'CINEMATIC': [8192,'256.0',5,3,4,3,4,4,2,4,4,3,3,3,0],
}
SCREENS = {
    'LIGHTING': 'SUN_INTENSITY NIGHT_BRIGHTNESS INDIRECT_QUALITY VOLUMETRIC_QUALITY',
    'TEMPORAL': 'TAA_QUALITY AA_QUALITY',
    'SHADOWS': 'shadowMapResolution shadowDistance SHADOW_QUALITY',
    'AO': 'AO_QUALITY',
    'ATMOSPHERE': 'TERRAIN_FOG_QUALITY FOG_DENSITY WIND_STRENGTH NIGHT_BRIGHTNESS',
    'CLOUDS': 'CLOUD_QUALITY CLOUD_COVERAGE CLOUD_SPEED',
    'WEATHER': 'WEATHER_QUALITY RAIN_INTENSITY RIPPLE_STRENGTH GODRAY_STRENGTH',
    'END_SKY': 'END_PLANETS END_ORBIT_SPEED',
    'WATER': 'WATER_QUALITY WATER_WAVES RIPPLE_STRENGTH SSR_QUALITY',
    'REFLECTIONS': 'SSR_QUALITY WET_SURFACES',
    'MATERIALS': 'PBR_MODE WET_SURFACES',
    'POST_PROCESS': 'BLOOM_QUALITY TONEMAP_MODE EXPOSURE AUTO_EXPOSURE SATURATION CONTRAST DOF_QUALITY MOTION_BLUR',
    'PERFORMANCE': 'shadowMapResolution shadowDistance TAA_QUALITY CLOUD_QUALITY WEATHER_QUALITY TERRAIN_FOG_QUALITY SSR_QUALITY AO_QUALITY INDIRECT_QUALITY VOLUMETRIC_QUALITY',
}

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8', newline='\n')

def shader_digest():
    digest=hashlib.sha256()
    for path in sorted(p for p in SHADERS.rglob('*') if p.is_file()):
        digest.update(path.relative_to(SHADERS).as_posix().encode())
        digest.update(b'\0'); digest.update(path.read_bytes()); digest.update(b'\0')
    return digest.hexdigest()

def generate():
    for folder, dim in [('',0),('world0',0),('world-1',-1),('world1',1)]:
        for name, (vert, frag, flags) in PROGRAMS.items():
            for ext, source in [('vsh',vert),('fsh',frag)]:
                content = '#version 330 compatibility\n'
                content += f'#define DIMENSION {dim}\n'
                content += ''.join(f'#define {flag}\n' for flag in flags)
                content += f'#include "/program/{source}.{ext}"\n'
                write(SHADERS / folder / f'{name}.{ext}', content)
    props = [
        f'# Galaxy Shader {VERSION} - Community Project',
        'clouds=off', 'sun=false', 'moon=false', 'stars=false',
        'oldLighting=false', 'oldHandLight=false', 'underwaterOverlay=false',
        'vignette=false', 'separateAo=true', 'frustum.culling=true',
        'shadow.culling=true', 'rain.depth=false', 'beacon.beam.depth=false',
        'particles.ordering=after',
        'size.buffer.colortex5=0.25 0.25', 'size.buffer.colortex6=0.25 0.25',
        'screen=<profile> [LIGHTING] [TEMPORAL] [SHADOWS] [AO] [ATMOSPHERE] [CLOUDS] [WEATHER] [END_SKY] [WATER] [REFLECTIONS] [MATERIALS] [POST_PROCESS] [PERFORMANCE]',
        'screen.columns=2',
        'sliders=CLOUD_COVERAGE CLOUD_SPEED WATER_WAVES RAIN_INTENSITY RIPPLE_STRENGTH GODRAY_STRENGTH EXPOSURE SATURATION CONTRAST FOG_DENSITY WIND_STRENGTH SUN_INTENSITY NIGHT_BRIGHTNESS',
    ]
    for name, values in PROFILES.items():
        props.append(f'profile.{name}='+' '.join(f'{k}:{v}' for k,v in zip(PROFILE_KEYS,values)))
    for name, options in SCREENS.items():
        props.append(f'screen.{name}={options}')
    for folder in ['', 'world0/', 'world-1/', 'world1/']:
        for name, (_,frag,_) in PROGRAMS.items():
            if frag == 'geometry':
                for attachment in [1,2,3]:
                    props.append(f'blend.{folder}{name}.colortex{attachment}=off')
            if frag in ['translucent','effect','weather']:
                props.append(f'alphaTest.{folder}{name}=off')
        props.append(f'blend.{folder}gbuffers_water=SRC_ALPHA ONE_MINUS_SRC_ALPHA ONE ONE_MINUS_SRC_ALPHA')
        props.append(f'blend.{folder}shadow=off')
    write(SHADERS/'shaders.properties','\n'.join(props)+'\n')
    labels = {
        'shadowMapResolution':('Shadow resolution','阴影分辨率'),
        'shadowDistance':('Shadow distance','阴影距离'),
        'SHADOW_QUALITY':('PCSS shadows','PCSS 柔和阴影'),
        'TAA_QUALITY':('Temporal anti-aliasing','时域抗锯齿'),
        'CLOUD_QUALITY':('Cloud quality','云层质量'),
        'CLOUD_COVERAGE':('Cloud coverage','云量'), 'CLOUD_SPEED':('Cloud speed','云速'),
        'WATER_QUALITY':('Water quality','水体质量'), 'WATER_WAVES':('Water waves','水波强度'),
        'SSR_QUALITY':('Screen-space reflections','屏幕空间反射'),
        'AO_QUALITY':('Ambient occlusion','环境光遮蔽'),
        'INDIRECT_QUALITY':('Indirect lighting','间接光照'),
        'VOLUMETRIC_QUALITY':('Volumetric light','体积光'),
        'WEATHER_QUALITY':('Weather quality','天气质量'),
        'TERRAIN_FOG_QUALITY':('Terrain fog quality','地形雾质量'),
        'RAIN_INTENSITY':('Rain intensity','雨线强度'),
        'RIPPLE_STRENGTH':('Rain ripple strength','雨滴涟漪强度'),
        'GODRAY_STRENGTH':('God ray strength','丁达尔光强度'),
        'BLOOM_QUALITY':('Bloom','泛光'), 'EXPOSURE':('Exposure','曝光'),
        'AUTO_EXPOSURE':('Eye adaptation','自动曝光'),
        'SATURATION':('Saturation','饱和度'), 'CONTRAST':('Contrast','对比度'),
        'FOG_DENSITY':('Fog density','雾浓度'), 'DOF_QUALITY':('Depth of field','景深'),
        'MOTION_BLUR':('Motion blur','动态模糊'), 'AA_QUALITY':('FXAA fallback','FXAA 后备抗锯齿'),
        'TONEMAP_MODE':('Tone mapping','色调映射'),
        'PBR_MODE':('LabPBR materials','LabPBR 材质'), 'WIND_STRENGTH':('Vegetation wind','植被风力'),
        'WET_SURFACES':('Wet surfaces','潮湿表面'), 'SUN_INTENSITY':('Sun intensity','阳光强度'),
        'NIGHT_BRIGHTNESS':('Night brightness','夜间亮度'),
        'END_PLANETS':('End planetary sky','末地行星天空'),
        'END_ORBIT_SPEED':('Orbital speed','行星公转速度'),
    }
    en_screens=['Lighting','Temporal','Shadows','Ambient Occlusion','Atmosphere','Clouds','Weather','End Sky','Water','Reflections','Materials','Post Processing','Performance']
    zh_screens=['光照','时域渲染','阴影','环境光遮蔽','大气','云层','天气','末地星空','水体','反射','材质','后期处理','性能']
    for lang,index in [('en_us',0),('zh_cn',1)]:
        lines=[f'option.{key}={values[index]}' for key,values in labels.items()]
        for i,key in enumerate(SCREENS):
            lines.append(f'screen.{key}={en_screens[i] if index==0 else zh_screens[i]}')
        quality=['Off','Low','Medium','High','Ultra'] if index==0 else ['关闭','低','中','高','极高']
        for option in ['CLOUD_QUALITY','WEATHER_QUALITY','SSR_QUALITY','AO_QUALITY','VOLUMETRIC_QUALITY','BLOOM_QUALITY','DOF_QUALITY','MOTION_BLUR']:
            for v in range(5): lines.append(f'value.{option}.{v}={quality[v]}')
        for v in range(4): lines.append(f'value.TERRAIN_FOG_QUALITY.{v}={quality[v]}')
        for v in range(1,5): lines.append(f'value.SHADOW_QUALITY.{v}={quality[v]}')
        lines.append(f'value.SHADOW_QUALITY.5={"Cinematic" if index==0 else "电影级"}')
        for option in ['AUTO_EXPOSURE','WET_SURFACES','END_PLANETS']:
            lines += [f'value.{option}.0={quality[0]}',f'value.{option}.1={"On" if index==0 else "开启"}']
        for v,label in enumerate(['Off','Auto (declared LabPBR)','Force LabPBR'] if index==0 else ['关闭','自动识别 LabPBR','强制 LabPBR']):
            lines.append(f'value.PBR_MODE.{v}={label}')
        lines += ['value.AA_QUALITY.0='+quality[0], 'value.AA_QUALITY.1=FXAA']
        for v,label in enumerate(['Off','Low','Medium','High'] if index==0 else ['关闭','低','中','高']):
            lines.append(f'value.TAA_QUALITY.{v}={label}')
        for v,label in enumerate(['Legacy Filmic','ACES-like','AgX-like'] if index==0 else ['传统 Filmic','类 ACES','类 AgX']):
            lines.append(f'value.TONEMAP_MODE.{v}={label}')
        lines += ['value.INDIRECT_QUALITY.0='+quality[0], 'value.INDIRECT_QUALITY.1='+quality[1], 'value.INDIRECT_QUALITY.2='+quality[3]]
        lines += [f'profile.{p}={p.title()}' for p in PROFILES]
        tips = {
            'END_PLANETS':('Four orbiting planets, a ringed giant, a central star and a fixed starfield. End only.','仅末地：四颗公转行星（含带环巨星）、中央恒星和固定星空。'),
            'END_ORBIT_SPEED':('0 freezes the planets; 0.5 / 1 / 2 changes orbital and axial speed.','0 为静止；0.5 / 1 / 2 倍速度同时控制公转与自转。'),
            'PBR_MODE':('Auto reads packs declaring LabPBR. Use Force only with an undeclared LabPBR pack.','自动读取声明 LabPBR 的资源包；仅对未声明格式的 LabPBR 包使用强制模式。'),
            'DOF_QUALITY':('For screenshots. Off by default.','推荐仅用于截图，默认关闭。'),
            'MOTION_BLUR':('Camera motion only. Excludes hand pixels. Off by default.','仅相机运动模糊，排除手持物区域，默认关闭。'),
            'AUTO_EXPOSURE':('Uses the temporally smoothed eye lightmap, with a bounded exposure gain.','使用平滑眼部亮度估算曝光，并限制提亮幅度。'),
            'SSR_QUALITY':('Off-screen rays fall back to sky or dim indoor environment.','屏幕外反射回退为天空或室内环境近似。'),
            'shadowMapResolution':('8192 consumes substantially more GPU memory.','8192 档会显著增加显存占用。'),
            'TAA_QUALITY':('Reprojects HDR history with depth rejection and neighborhood clamping; FXAA remains optional.','重投影 HDR 历史，并使用深度拒绝和邻域裁剪；FXAA 仍可选。'),
            'SHADOW_QUALITY':('Medium and above use contact-hardening PCSS; Low uses a four-tap PCF fallback.','中档及以上使用接触硬化 PCSS；低档使用四采样 PCF 后备。'),
            'AO_QUALITY':('Directional horizon AO uses a world-space radius and edge-aware samples.','方向性地平线 AO 使用世界空间半径与边缘感知采样。'),
            'TONEMAP_MODE':('AgX-like is the natural-color default; ACES-like and the legacy curve remain available.','默认类 AgX 以保持自然色彩；也可选择类 ACES 与传统曲线。'),
            'WEATHER_QUALITY':('Controls procedural rain layers, surface splashes and water ripples. Off restores the lightweight fallback.','控制程序化雨线层次、地表飞溅和水面涟漪；关闭时使用轻量后备效果。'),
            'TERRAIN_FOG_QUALITY':('Adds height, valley and distance fog with terrain depth occlusion.','加入高度雾、山谷雾与远景霾，并由地形深度遮挡。'),
            'RAIN_INTENSITY':('Scales procedural rain visibility without changing Minecraft weather state.','缩放程序化雨线可见度，不改变 Minecraft 天气状态。'),
            'RIPPLE_STRENGTH':('Scales expanding rain rings on water and small impacts on exposed surfaces.','缩放水面扩散雨纹与暴露表面的细小落雨冲击。'),
            'GODRAY_STRENGTH':('Scales shadow-mapped dawn and dusk shafts; midday is reduced automatically.','缩放带阴影遮挡的晨昏光柱；正午会自动减弱。'),
        }
        lines += [f'option.{k}.comment={v[index]}' for k,v in tips.items()]
        write(SHADERS/'lang'/f'{lang}.lang','\n'.join(lines)+'\n')

def package():
    from validate import static_checks
    static_checks()
    digest=shader_digest()
    compile_report=json.loads((ROOT/'validation/compile-report.json').read_text(encoding='utf-8'))
    render_report=json.loads((ROOT/'validation/render-report.json').read_text(encoding='utf-8'))
    directive_report=json.loads((ROOT/'validation/iris-directive-report.json').read_text(encoding='utf-8'))
    assert compile_report.get('driver_compile')=='passed','Run full GPU compile validation first'
    assert compile_report.get('full_matrix') is True,'Quick validation is insufficient for release'
    assert directive_report.get('status')=='passed','Run the Iris directive parser check first'
    for report in [compile_report,render_report,directive_report]:
        assert report.get('shader_sha256')==digest,'Validation is stale; rerun after source changes'
    output=ROOT/f'Galaxy Shader-{VERSION}.zip'
    files=sorted(p for p in PACK.rglob('*') if p.is_file())
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files:
            info=zipfile.ZipInfo(path.relative_to(PACK).as_posix(), (2026,9,6,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    with zipfile.ZipFile(output) as z:
        assert 'shaders/shaders.properties' in z.namelist()
        assert z.testzip() is None
        assert not any(name.startswith('Galaxy Shader/') for name in z.namelist())
        for path in files: assert z.read(path.relative_to(PACK).as_posix())==path.read_bytes()
    sha=hashlib.sha256(output.read_bytes()).hexdigest()
    write(ROOT/(output.name+'.sha256'),f'{sha}  {output.name}\n')
    write(ROOT/'validation/release-manifest.json',json.dumps({'archive_sha256':sha,'shader_sha256':digest,
          'files':len(files),'zip_root':'shaders/','archive_verified':True,'game_acceptance':'pending'},indent=2)+'\n')
    print(json.dumps({'zip':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':sha}))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',action='store_true')
    args=parser.parse_args()
    generate()
    if args.package: package()
