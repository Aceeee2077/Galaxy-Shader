#ifndef SE_CLOUD_IRIDESCENCE
#define SE_CLOUD_IRIDESCENCE
#include "/lib/noise.glsl"

// Iridescence in thin high cloud: small, uniform droplets diffract sunlight
// into pastel fringes, strongest within roughly 5 to 30 degrees of the sun.
// The patch mask is analytic and represents a thin cloud veil, not the main
// cloud deck, so no texture, lookup table or render target is added.
vec3 cloudIridescence(vec3 ray, vec3 sun, float day, float overcast) {
    if (day <= 0.0 || overcast >= 0.98 || sun.y <= 0.02) return vec3(0.0);
    float cosAngle = dot(ray, sun);
    if (cosAngle < 0.80) return vec3(0.0); // about 37 degrees
    float angle = acos(clamp(cosAngle, -1.0, 1.0));
    if (angle < 0.035) return vec3(0.0);

    // A thin, broken veil around the sun. The two scales give soft sheets with
    // smaller wisps inside them, and the whole field drifts very slowly.
    float azimuth = atan(ray.z, ray.x);
    float elevation = asin(clamp(ray.y, -1.0, 1.0));
    float drift = frameTimeCounter * 0.0025;
    float sheet = valueNoise(vec2(azimuth * 2.6 + drift, elevation * 5.0 - drift));
    float wisp = valueNoise(vec2(azimuth * 7.4 - drift * 0.6,
                                 elevation * 13.0 + 9.1));
    // Break the veil into separated thin-cloud patches so the fringes show as
    // coloured arcs inside cloud, not as a bullseye painted on a clear sky.
    float patch = valueNoise(vec2(azimuth * 4.3 - drift * 0.4,
                                  elevation * 9.7 + 4.7));
    float veil = smoothstep(0.46, 0.68, sheet * 0.62 + wisp * 0.38) *
                 smoothstep(0.38, 0.62, patch);
    if (veil <= 0.0) return vec3(0.0);

    // Diffraction order: the pastel sequence repeats slowly with angle, and
    // the veil nudges each fringe so edges are not perfectly circular.
    float order = angle * 46.0 + wisp * 2.4 + sheet * 0.9;
    vec3 fringe = 0.55 + 0.45 * cos(6.2831853 *
                   (order + vec3(0.00, 0.33, 0.67)));
    float radial = smoothstep(0.035, 0.11, angle) *
                   (1.0 - smoothstep(0.34, 0.50, angle));
    return fringe * veil * radial * day * (1.0 - sat(overcast)) * 0.055;
}
#endif
