#ifndef SE_WATER
#define SE_WATER
#include "/lib/weather.glsl"
// Wind-driven whitecaps: only a steep wave slope with a matching noise crest
// produces foam, and storms add more. Calm water is exactly zero.
float crestFoamAmount(vec2 slope, float noise, float storm) {
    float steep = smoothstep(0.12, 0.45, length(slope));
    float broken = smoothstep(0.52, 0.82, noise);
    return steep * broken * (0.35 + 0.65 * sat(storm));
}

// Small spectral separation for the top water profile. The red channel samples
// slightly to one side of the refracted UV and blue to the other; green stays
// on the physical UV so the image does not shift as a whole.
vec3 chromaticRefraction(sampler2D scene, vec2 uv, vec2 offset) {
    vec2 lo=clamp(uv+offset,pixelSize(),1.0-pixelSize());
    vec2 hi=clamp(uv-offset,pixelSize(),1.0-pixelSize());
    return vec3(texture2D(scene,lo).r, texture2D(scene,uv).g,
                texture2D(scene,hi).b);
}
vec3 waterNormal(vec3 world, vec3 geometric, float distanceToEye) {
    float t=frameTimeCounter;
    vec2 gradient=vec2(0.0);
#if WATER_QUALITY > 0
    int waves=min(WATER_QUALITY+1,3);
    for(int i=0;i<3;++i) {
        if(i>=waves) break;
        float fi=float(i);
        vec2 dir=vec2(cos(fi*2.17+0.2),sin(fi*2.17+0.2));
        float frequency=0.65+fi*1.45;
        float amplitude=0.043/(1.0+fi);
        vec2 crossDir=vec2(-dir.y,dir.x);
        float modulation=sin(dot(world.xz,crossDir)*0.37-t*0.28)*0.65;
        gradient+=dir*cos(dot(world.xz,dir)*frequency+t*(0.9+fi*0.31)+modulation)*amplitude;
    }
#if WATER_QUALITY >= 2
    // Small capillary slopes break the low sun's reflection into moving glints
    // along its physical reflection path instead of a single smooth patch.
    gradient+=vec2(sin(world.x*4.7+world.z*0.8-t*2.5),
                   sin(world.z*5.3-world.x*0.6+t*2.1))*0.008;
#endif
#if WATER_QUALITY >= 3
    // A second, higher-frequency capillary train. The amplitude is small so it
    // reads as micro-roughness on the glints, not as another visible wave.
    gradient+=vec2(sin(world.x*9.3-world.z*2.1+t*3.7),
                   sin(world.z*8.7+world.x*1.6-t*3.1))*0.0035;
#endif
    float rain=weatherRainAmount();
    if(rain>0.001) {
        vec3 ripple=rainRippleField(world.xz,1.35);
        gradient+=ripple.xy*rain*RIPPLE_STRENGTH*0.052;
        vec2 wind=weatherWindDirection();
        gradient+=wind*sin(dot(world.xz,wind)*13.0-t*(5.0+weatherStormAmount()*4.0))*
                  rain*(0.012+weatherStormAmount()*0.014);
    }
#endif
    gradient*=WATER_WAVES/(1.0+distanceToEye*0.012);
    return safeNormalize(geometric+vec3(gradient.x,0,gradient.y)*abs(geometric.y));
}
#endif
