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
    if (!soft) return step(coord.z-bias,texture2D(shadowtex0,coord.xy).r);

    float distanceFade = length(player.xz) / shadowDistance;
    float sunStretch = 1.0 + 1.35 * (1.0 - abs(sunDirection().y));
    float angle = hash12(floor((player.xz + cameraPosition.xz) * 0.25)) * 2.0 * PI;
    mat2 rotation = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));

#if SHADOW_QUALITY == 1
    const int blockerSamples = 0;
    const int filterSamples = 4;
#elif SHADOW_QUALITY == 2
    const int blockerSamples = 6;
    const int filterSamples = 8;
#elif SHADOW_QUALITY == 3
    const int blockerSamples = 8;
    const int filterSamples = 12;
#elif SHADOW_QUALITY == 4
    const int blockerSamples = 12;
    const int filterSamples = 16;
#else
    const int blockerSamples = 16;
    const int filterSamples = 24;
#endif

    // PCSS blocker search: only depths in front of the receiver can cast here.
    float blockerDepth = 0.0;
    float blockers = 0.0;
#if SHADOW_QUALITY > 1
    float searchRadius = (1.2 + 2.0 * distanceFade) * sunStretch /
                         float(shadowMapResolution);
    for (int i = 0; i < blockerSamples; ++i) {
        vec2 sampleUV = coord.xy + rotation * diskSample(i, blockerSamples) * searchRadius;
        float sampleDepth = texture2D(shadowtex0, sampleUV).r;
        if (sampleDepth < coord.z - bias) {
            blockerDepth += sampleDepth;
            blockers += 1.0;
        }
    }
#endif

    float filterRadiusTexels = 0.8;
    if (blockers > 0.0) {
        blockerDepth /= blockers;
        // Contact hardening: receiver/blocker separation grows the penumbra.
        float separation = max(coord.z - blockerDepth, 0.0) /
                           max(blockerDepth, 0.02);
        float lightSize = 34.0 * sunStretch;
        filterRadiusTexels = clamp(0.55 + separation * lightSize, 0.55,
                                   2.2 + float(SHADOW_QUALITY) * 0.9);
    }
    // Preserve the 1.3 far-distance budget reduction.
    int count = distanceFade > 0.6 ? min(filterSamples, 4) : filterSamples;
    float visibility = 0.0;
    for (int i = 0; i < filterSamples; ++i) {
        if (i >= count) break;
        vec2 offset = rotation * diskSample(i, count) * filterRadiusTexels /
                      float(shadowMapResolution);
        visibility += step(coord.z-bias,texture2D(shadowtex0,coord.xy+offset).r);
    }
    visibility /= float(count);
    float fade = smoothstep(shadowDistance*0.75,shadowDistance*0.98,length(player.xz));
    return mix(visibility,1.0,fade);
#endif
}
#endif
