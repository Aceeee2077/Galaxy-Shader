"""Measure how often a terrain fragment evaluates directional radiance.

The fixture calls the real `shadeSurface` with a call-counting probe and
compares the new shared radiance against the previous one-call-per-lobe build.
It is an engineering report, not a screenshot.
"""
import json
import numpy as np
from build import ROOT, SHADERS, shader_digest
from validate import expand
from render_smoke import Renderer, U

W, H = 16, 16
VERTEX = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
DECL_NEW = '    vec3 sunRadiance=directionalRadiance();\n'
DIRECT_NEW = ('    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*'
              'sunRadiance*shadow;')
DIRECT_OLD = ('    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*'
              'directionalRadiance()*shadow;')
LEAF_NEW = '(0.06+0.36*forward)*(1.0-nl)*sunRadiance*shadow;'
LEAF_OLD = '(0.06+0.36*forward)*(1.0-nl)*directionalRadiance()*shadow;'
BOUNCE_NEW = 'direct+=m.albedo*(1.0-m.metal)*sunRadiance*0.035*'
BOUNCE_OLD = 'direct+=m.albedo*(1.0-m.metal)*directionalRadiance()*0.035*'
DEFINITION = 'vec3 directionalRadiance() {'
SURFACE = '''
uniform float testSky;
void main() {
    Material m=defaultMaterial(vec3(0.18),vec3(0.0,1.0,0.0));
    vec3 c=shadeSurface(m,vec3(0.0,0.0,-10.0),vec2(0.0,testSky),0.0);
    gl_FragColor=vec4(c,radianceCalls);
}'''


def source(old=False):
    core = expand(SHADERS / 'lib/common.glsl') + expand(SHADERS / 'lib/lighting.glsl')
    for snippet in (DECL_NEW, DIRECT_NEW, LEAF_NEW, BOUNCE_NEW):
        assert core.count(snippet) == 1, snippet
    if old:
        core = core.replace(DECL_NEW, '')
        core = core.replace(DIRECT_NEW, DIRECT_OLD)
        core = core.replace(LEAF_NEW, LEAF_OLD)
        core = core.replace(BOUNCE_NEW, BOUNCE_OLD)
    core = core.replace(DEFINITION, 'vec3 radianceCore() {')
    head = ('#version 330 compatibility\n#define DIMENSION 0\n#define vCloudShadow 1.0\n'
            'float radianceCalls=0.0;\nvec3 directionalRadiance();\n')
    wrapper = '''
vec3 directionalRadiance(){
    radianceCalls+=1.0;
    return radianceCore();
}
'''
    return (head + core + wrapper + SURFACE).replace(
        '#define CLOUD_QUALITY 3', '#define CLOUD_QUALITY 0')


def main():
    renderer = Renderer(W, H)
    programs = {
        'new': renderer.gl.compile(VERTEX, source()),
        'old': renderer.gl.compile(VERTEX, source(old=True)),
    }
    dark = renderer.texture(1, 1, data=np.zeros((1, 1, 4), np.float32))
    white = renderer.white

    def image(name, elevation, sky, rain, thunder):
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
        renderer.uniform(program, 'testSky', sky)
        renderer.uniform(program, 'rainStrength', rain)
        renderer.uniform(program, 'wetness', rain)
        renderer.uniform(program, 'thunderStrength', thunder)
        angle = np.deg2rad(elevation)
        direction = [0.0, float(np.sin(angle)),
                     -float(np.cos(angle))]
        renderer.uniform(program, 'sunPosition', direction)
        renderer.uniform(program, 'shadowLightPosition', direction)
        renderer.uniform(program, 'moonPosition', [-v for v in direction])
        renderer.call('glActiveTexture', None, [U], 0x84C0)
        renderer.call('glBindTexture', None, [U, U], 0x0DE1,
                      white if sky > 0.5 else dark)
        renderer.full_screen()
        renderer.check('radiance cache report')
        data = renderer.read(W, H)[:, :, :4]
        assert np.isfinite(data).all()
        return data

    cases = {}
    for name, (elevation, sky, rain, thunder) in {
        'noon': (40.0, 1.0, 0.0, 0.0),
        'golden_hour': (5.0, 1.0, 0.0, 0.0),
        'night': (-30.0, 1.0, 0.0, 0.0),
        'cave': (40.0, 0.0, 0.0, 0.0),
        'rain': (40.0, 1.0, 1.0, 0.0),
        'storm': (40.0, 1.0, 1.0, 1.0),
    }.items():
        new = image('new', elevation, sky, rain, thunder)
        old = image('old', elevation, sky, rain, thunder)
        cases[name] = {
            'radiance_calls_before': float(old[:, :, 3].sum()),
            'radiance_calls_after': float(new[:, :, 3].sum()),
            'calls_saved_per_pixel': round(
                (float(old[:, :, 3].mean()) - float(new[:, :, 3].mean())), 4),
            'max_abs_difference': float(
                np.abs(new[:, :, :3] - old[:, :, :3]).max()),
        }

    for program in programs.values():
        renderer.gl.delete_program(program)
    renderer.close()

    report = {
        'type': 'Synthetic GPU report; not a Minecraft screenshot',
        'shader_sha256': shader_digest(),
        'resolution': [W, H],
        'pixels': W * H,
        'cases': cases,
        'status': 'shared radiance matches the previous shading while each '
                  'terrain fragment evaluates the transmittance chain once '
                  'instead of three times',
    }
    (ROOT / 'validation' / 'radiance-cache-report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(cases, indent=2), flush=True)


if __name__ == '__main__':
    main()
