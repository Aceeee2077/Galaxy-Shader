#ifndef SE_TWILIGHT_OPTICS
#define SE_TWILIGHT_OPTICS
#include "/lib/noise.glsl"

// Three naked-eye sky phenomena share this file: the Earth's shadow and the
// Belt of Venus on the anti-solar horizon at twilight, the zodiacal light cone
// above the set point of the sun, and upper-atmosphere airglow after dark.
// All are analytic. None adds a texture, lookup table or render target.

// Cosine of the angle between a ray's horizontal projection and the anti-solar
// azimuth. It stays meaningful only for the low elevations used below; a ray
// close to the zenith has almost no horizontal component, so callers restrict
// their elevation windows instead of normalising an unstable direction.
float antiSolarArc(vec3 ray, vec3 sun) {
    vec2 rayHorizontal = ray.xz;
    vec2 sunHorizontal = -sun.xz;
    float rayLength = length(rayHorizontal);
    float sunLength = length(sunHorizontal);
    if (rayLength < 1e-4 || sunLength < 1e-4) return 0.0;
    return clamp(dot(rayHorizontal / rayLength, sunHorizontal / sunLength), 0.0, 1.0);
}

// The dark blue-grey wedge rising from the anti-solar horizon: the Earth's
// shadow projected onto the atmosphere. It grows as the sun sinks and dissolves
// before astronomical twilight, when the sky is no longer lit from below.
float earthShadowMask(vec3 ray, vec3 sun) {
    float h = ray.y;
    if (h < 0.0) return 0.0;
    float gate = smoothstep(-0.32, -0.10, sun.y) *
                 (1.0 - smoothstep(-0.01, 0.055, sun.y));
    float top = clamp(0.018 + max(-sun.y, 0.0) * 0.52, 0.02, 0.16);
    float wedge = smoothstep(0.0, 0.018, h) *
                  (1.0 - smoothstep(top - 0.028, top + 0.018, h));
    return wedge * pow(antiSolarArc(ray, sun), 0.7) * gate;
}

// The pink fringe that caps the shadow. It is a narrow band rather than a
// second sunset: its centre tracks the shadow top, and it fades out before the
// blue-hour dome takes over.
vec3 beltOfVenus(vec3 ray, vec3 sun) {
    float h = ray.y;
    if (h < 0.0 || h > 0.42) return vec3(0.0);
    float gate = smoothstep(-0.24, -0.075, sun.y) *
                 (1.0 - smoothstep(-0.005, 0.05, sun.y));
    float top = clamp(0.018 + max(-sun.y, 0.0) * 0.52, 0.02, 0.16);
    float centre = top + 0.045;
    float band = exp(-pow((h - centre) / 0.050, 2.0)) *
                 smoothstep(0.0, 0.025, h);
    float arc = antiSolarArc(ray, sun);
    vec3 colour = mix(vec3(0.42, 0.15, 0.18), vec3(0.52, 0.28, 0.20), arc);
    return colour * 0.085 * band * pow(arc, 0.8) * gate;
}

// Zodiacal light: sunlight forward-scattered by interplanetary dust along the
// ecliptic. In Minecraft it is approximated as a soft cone above the sun's
// azimuth, widening with elevation. It appears after the sun has set and is
// gone by full darkness, when it is too faint for this exposure range.
vec3 zodiacalLight(vec3 ray, vec3 sun) {
    float h = ray.y;
    if (h < 0.0 || h > 0.75) return vec3(0.0);
    float gate = smoothstep(-0.45, -0.22, sun.y) *
                 (1.0 - smoothstep(-0.04, 0.03, sun.y));
    vec2 sunHorizontal = sun.xz;
    float sunLength = length(sunHorizontal);
    if (sunLength < 1e-4) return vec3(0.0);
    vec2 rayHorizontal = normalize(ray.xz + vec2(1e-5));
    float angle = acos(clamp(dot(rayHorizontal, sunHorizontal / sunLength), -1.0, 1.0));
    float spread = 0.14 + 0.75 * h;
    float cone = exp(-pow(angle / spread, 2.0));
    float vertical = smoothstep(0.0, 0.04, h) * exp(-h * 2.2) *
                     (1.0 - smoothstep(0.50, 0.72, h));
    return vec3(0.58, 0.52, 0.38) * 0.040 * cone * vertical * gate;
}

// Airglow: faint chemiluminescence of the upper atmosphere. A broad layer
// peaking around 10 degrees, weighted green near the horizon and blue-green
// higher up, with slow wave structure. The drift is intentionally much slower
// than the clouds so it reads as a sky phenomenon and not weather.
vec3 airglow(vec3 ray, vec3 sun) {
    float h = ray.y;
    if (h < 0.0 || h > 0.9) return vec3(0.0);
    float night = smoothstep(0.03, 0.20, -sun.y);
    float layer = exp(-pow((h - 0.12) / 0.18, 2.0));
    float azimuth = atan(ray.z, ray.x);
    float drift = frameTimeCounter * 0.006;
    float broadWave = valueNoise(vec2(azimuth * 2.3 + drift, h * 6.0 - drift * 0.5));
    float fineWave = valueNoise(vec2(azimuth * 6.1 - drift * 0.7, h * 14.0 + 11.0));
    float structure = 0.50 + 0.38 * broadWave + 0.22 * fineWave;
#if AIRGLOW_RIPPLES > 0
    // Gravity waves in the airglow layer read as faint parallel bands. Their
    // phase bends with azimuth so they never look like a flat scan line.
    float rippleWarp = sin(azimuth * 1.7 + drift * 0.35) * 0.45 +
                       sin(azimuth * 4.1 - drift * 0.18) * 0.18;
    float ripplePhase = h * 46.0 + rippleWarp * 5.0 - drift * 0.8;
    float ripples = pow(0.5 + 0.5 * cos(ripplePhase), 3.0);
    structure *= 0.70 + 0.60 * ripples;
#endif
    vec3 tint = mix(vec3(0.09, 0.30, 0.17), vec3(0.06, 0.19, 0.16),
                    smoothstep(0.0, 0.45, h));
    return tint * 0.020 * layer * structure * night;
}

// Additive sky contribution. The Earth's shadow multiplies the twilight dome
// instead, so it stays a darkening effect and can never become a coloured glow.
vec3 twilightOptics(vec3 ray, vec3 sun, float overcast) {
    float clear = 1.0 - clamp(overcast, 0.0, 1.0);
    return (beltOfVenus(ray, sun) + zodiacalLight(ray, sun) + airglow(ray, sun)) *
           clear;
}

#endif
