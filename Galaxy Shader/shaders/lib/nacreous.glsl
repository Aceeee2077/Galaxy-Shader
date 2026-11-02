#ifndef SE_NACREOUS
#define SE_NACREOUS
#include "/lib/noise.glsl"

// Polar stratospheric clouds form near 25 km and catch sunlight after the lower
// sky has darkened. Thin ice and nitric-acid crystals diffract the light into
// pastel lenticular sheets. The layer is projected onto a horizontal plane,
// gated to a narrow twilight window and weighted toward winter.
vec3 nacreousClouds(vec3 ray, vec3 sun, float overcast, float winter) {
    float h = ray.y;
    if (h < 0.018 || h > 0.58) return vec3(0.0);

    // Roughly 2-13 degrees of solar depression: below the warm twilight layer
    // but before the mesosphere goes completely dark.
    float solarGate = smoothstep(-0.23, -0.13, sun.y) *
                      (1.0 - smoothstep(-0.038, -0.012, sun.y));
    float clearGate = 1.0 - sat(overcast);
    if (solarGate * clearGate <= 1e-4) return vec3(0.0);

    vec2 plane = ray.xz / max(h, 0.045);
    vec2 drift = vec2(frameTimeCounter * 0.0032, frameTimeCounter * 0.0011);
    float broad = fbm(plane * 0.50 + drift, 4);
    float lenticular = smoothstep(0.44, 0.68, broad);
    if (lenticular <= 1e-4) return vec3(0.0);

    float detail = fbm(plane * 1.75 - drift * 0.45 + vec2(3.7, 9.1), 3);
    float streaks = smoothstep(0.38, 0.70, detail);
    float sheet = lenticular * (0.55 + 0.45 * streaks);

    // Iridescence comes from diffraction, so its hue drifts across the cloud
    // sheet instead of following a fixed gradient. Three phase-offset cosines
    // give pastel pink, green and blue bands; most saturation is removed so the
    // result stays a high, thin cloud rather than a rainbow.
    float iridPhase = broad * 4.0 + detail * 2.2 + h * 9.0 +
                      atan(ray.z, ray.x) * 0.55;
    vec3 pastel = 0.5 + 0.5 * cos(iridPhase * 6.2831853 +
                                  vec3(0.0, 2.094, 4.188));
    pastel = mix(vec3(0.72, 0.75, 0.86), pastel, 0.55);

    float elevationFade = smoothstep(0.018, 0.075, h) *
                          (1.0 - smoothstep(0.30, 0.55, h));
    float winterGate = 0.12 + 0.88 * sat(winter);
    return pastel * sheet * elevationFade * solarGate * winterGate *
           clearGate * 0.11;
}
#endif
