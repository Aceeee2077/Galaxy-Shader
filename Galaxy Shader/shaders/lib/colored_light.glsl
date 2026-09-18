#ifndef SE_COLORED_LIGHT
#define SE_COLORED_LIGHT
#include "/lib/noise.glsl"

// Screen-space colored light propagation. Emissive surfaces visible in the
// current frame act as point-like sources and tint nearby geometry in screen
// space. This is a bounded Iris 1.6-friendly approximation of Photon's voxel
// flood-fill: it cannot reach emitters that are off-screen or fully occluded,
// but it reproduces the colored torch/glowstone/lava glow on visible surfaces.
vec3 screenColoredLight(vec2 uv, vec3 view, vec3 worldNormal) {
    vec3 light = vec3(0.0);
#if COLORED_LIGHT_QUALITY > 0
    vec3 n = safeNormalize(mat3(gbufferModelView) * worldNormal);
    float worldRadius = 2.0 + float(COLORED_LIGHT_QUALITY) * 2.0;
    vec2 radiusUV = vec2(gbufferProjection[0][0], gbufferProjection[1][1]) *
                    worldRadius / max(-view.z, 1.0) * 0.5;
    radiusUV = min(radiusUV, vec2(0.22));
    int count = COLORED_LIGHT_QUALITY * 6;

    for (int i = 0; i < 18; ++i) {
        if (i >= count) break;
        vec2 suv = uv + diskSample(i, count) * radiusUV;
        if (screenInside(suv) < 0.5) continue;
        float depth = texture2D(depthtex1, suv).r;
        if (skyDepth(depth) > 0.5) continue;
        vec4 meta = texture2D(colortex3, suv);
        if (meta.g < 0.015 || meta.b > 0.5) continue;

        vec3 sourceView = viewPosition(suv, depth);
        vec3 delta = sourceView - view;
        float dist = length(delta);
        if (dist > worldRadius) continue;
        float depthSimilarity = 1.0 - smoothstep(0.0, worldRadius, abs(delta.z));
        if (depthSimilarity <= 0.0) continue;
        float facing = sat(dot(n, delta / max(dist, 0.001)));
        float falloff = 1.0 / (1.0 + dist * dist * 1.6);
        vec3 sourceColor = texture2D(colortex2, suv).rgb;
        light += sourceColor * meta.g * falloff * facing * depthSimilarity;
    }
    light *= 0.18;
#endif
    return light;
}
#endif
