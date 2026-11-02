#ifndef SE_SECONDARY_RAINBOW
#define SE_SECONDARY_RAINBOW

// The secondary rainbow sits near 51 degrees from the anti-solar point, about
// nine degrees outside the primary. Two internal reflections dim it to roughly
// a tenth of the primary and reverse the colour order: red is now on the inner
// edge and violet on the outer. It shares the rain or lingering-wetness gate.
vec3 secondaryRainbow(vec3 ray, vec3 sun, float moisture, float overcast,
                      float day) {
    if (moisture <= 0.025 || sun.y <= 0.02 || ray.y <= 0.0) return vec3(0.0);
    float angle = acos(clamp(dot(ray, -sun), -1.0, 1.0));
    const float inner = 0.880; // 50.4 degrees
    const float span = 0.072;  // about 4.1 degrees to the violet edge
    float spectral = (angle - inner) / span;
    if (spectral <= 0.0 || spectral >= 1.0) return vec3(0.0);

    float edge = smoothstep(0.0, 0.10, spectral) *
                 (1.0 - smoothstep(0.90, 1.0, spectral));
    // Red on the inside, then yellow, green, blue and violet outside.
    vec3 bow = mix(vec3(0.96, 0.20, 0.06), vec3(0.94, 0.80, 0.16),
                   smoothstep(0.05, 0.30, spectral));
    bow = mix(bow, vec3(0.16, 0.78, 0.34), smoothstep(0.29, 0.55, spectral));
    bow = mix(bow, vec3(0.16, 0.42, 0.95), smoothstep(0.54, 0.78, spectral));
    bow = mix(bow, vec3(0.52, 0.24, 0.92), smoothstep(0.77, 0.96, spectral));

    float clearSky = 1.0 - overcast * 0.72;
    return bow * edge * smoothstep(0.0, 0.10, ray.y) *
           moisture * clearSky * day * 0.085;
}
#endif
