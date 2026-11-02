#ifndef SE_NOCTILUCENT
#define SE_NOCTILUCENT
#include "/lib/noise.glsl"

// Noctilucent clouds: a thin, high mesospheric ice layer that stays sunlit long
// after the lower atmosphere has gone dark. They are drawn directly into the
// sky as an additive blue-white veil, with no texture, render target or extra
// cloud march. The pattern is projected onto a horizontal plane so it behaves
// like a layer above the player rather than a screen-space overlay.
vec3 noctilucentClouds(vec3 ray, vec3 sun, float overcast, float summer) {
    float h = ray.y;
    if (h < 0.012 || h > 0.62) return vec3(0.0);
    // The layer is visible only while the sun is below the horizon but still
    // above the mesopause: roughly the -2 to -26 degree solar window.
    float solarGate = smoothstep(-0.45, -0.28, sun.y) *
                      (1.0 - smoothstep(-0.055, -0.012, sun.y));
    // Noctilucent clouds peak in polar summer. Keep a base visibility so the
    // effect can be inspected in any season, then strengthen it in summer.
    float summerGate = 0.35 + 0.65 * sat(summer);
    float clearGate = 1.0 - sat(overcast);
    if (solarGate * clearGate < 1e-4) return vec3(0.0);

    // Plane projection: rays near the horizon stretch far away, which gives the
    // banded, perspective-correct look of a real high cloud layer.
    vec2 plane = ray.xz / max(h, 0.035);
    vec2 drift = vec2(frameTimeCounter * 0.0045, -frameTimeCounter * 0.0021);
    float broad = fbm(plane * 0.42 + drift, 4);
    float fine = fbm(plane * 1.15 - drift * 0.7 + vec2(7.3, 2.1), 3);
    float ridged = 1.0 - abs(2.0 * fine - 1.0);
    float pattern = broad * 0.62 + ridged * 0.46;
    float coverage = smoothstep(0.43, 0.74, pattern);
    if (coverage < 1e-4) return vec3(0.0);

    // Slow wave trains run through the sheet. They fade with elevation so the
    // high part of the layer does not turn into a hard striped band.
    float wave = 0.55 + 0.45 * sin(plane.y * 1.7 + broad * 4.2 +
                                   frameTimeCounter * 0.010);
    float elevationFade = smoothstep(0.012, 0.07, h) *
                          (1.0 - smoothstep(0.30, 0.58, h));
    vec3 tint = mix(vec3(0.30, 0.55, 0.95), vec3(0.78, 0.89, 1.0),
                    smoothstep(0.52, 0.88, pattern));
    return tint * coverage * wave * elevationFade *
           solarGate * summerGate * clearGate * 0.055;
}

#endif
