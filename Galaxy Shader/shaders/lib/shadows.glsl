#ifndef SE_SHADOWS
#define SE_SHADOWS
#include "/lib/noise.glsl"
uniform sampler2D shadowtex0;
vec3 shadowCoordinate(vec3 player) {
    vec4 p = shadowProjection*shadowModelView*vec4(player,1.0);
    return p.xyz/max(abs(p.w),1e-6)*0.5+0.5;
}
float shadowVisibility(vec3 player, vec3 normal, bool soft) {
#if DIMENSION != 0
    return 1.0;
#else
    float texelWorld = 2.0*shadowDistance/float(shadowMapResolution);
    float slope = 1.0-sat(dot(normal,lightDirection()));
    vec3 coord = shadowCoordinate(player+normal*texelWorld*(0.55+0.9*slope));
    if (any(lessThan(coord,vec3(0.003))) || any(greaterThan(coord,vec3(0.997)))) return 1.0;
    float bias = 0.00008+0.00015*slope;
    float visibility = 0.0;
    int count = soft ? SHADOW_QUALITY*4 : 1;
    if (soft && length(player.xz) > shadowDistance*0.6) count = 4;
    float radius = soft ? (0.7+float(SHADOW_QUALITY)*0.22+length(player)/shadowDistance)*
                    (1.0+1.5*(1.0-abs(sunDirection().y))) : 0.0;
    for (int i=0;i<16;++i) {
        if (i>=count) break;
        vec2 offset = diskSample(i,count)*radius/float(shadowMapResolution);
        visibility += step(coord.z-bias,texture2D(shadowtex0,coord.xy+offset).r);
    }
    visibility /= float(count);
    float fade = smoothstep(shadowDistance*0.75,shadowDistance*0.98,length(player.xz));
    return mix(visibility,1.0,fade);
#endif
}
#endif
