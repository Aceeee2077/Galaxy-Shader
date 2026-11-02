#ifndef SE_MOONBOW
#define SE_MOONBOW

// A lunar rainbow uses the same 42-degree refraction geometry as the solar one,
// but moonlight is far too weak for the eye to resolve strong colour. The arc
// is therefore desaturated toward silver and tinted cool, with only a trace of
// the spectral order remaining. It requires rain, a moon above the horizon and
// a moonlit fraction large enough to illuminate the drops.
vec3 moonbow(vec3 ray, vec3 moonDir, float litFraction, float moisture,
             float night, float overcast) {
    if (moisture <= 0.025 || night <= 0.0 || litFraction <= 0.08) return vec3(0.0);
    if (ray.y <= 0.0 || moonDir.y <= 0.015) return vec3(0.0);

    float angle = acos(clamp(dot(ray, -moonDir), -1.0, 1.0));
    float spectral = (angle - 0.655) / 0.145;
    if (spectral <= 0.0 || spectral >= 1.0) return vec3(0.0);

    float edge = smoothstep(0.0, 0.09, spectral) *
                 (1.0 - smoothstep(0.91, 1.0, spectral));
    vec3 bow = mix(vec3(0.40, 0.16, 0.74), vec3(0.10, 0.32, 0.95),
                   smoothstep(0.06, 0.24, spectral));
    bow = mix(bow, vec3(0.06, 0.80, 0.40), smoothstep(0.23, 0.46, spectral));
    bow = mix(bow, vec3(0.98, 0.86, 0.12), smoothstep(0.46, 0.68, spectral));
    bow = mix(bow, vec3(1.0, 0.22, 0.07), smoothstep(0.68, 0.94, spectral));

    // Desaturate most of the way to moonlit grey, then apply a cool cast.
    bow = mix(vec3(luminance(bow)), bow, 0.30) * vec3(0.76, 0.85, 1.0);
    float clearSky = 1.0 - 0.72 * overcast;
    float visibility = night * clearSky * moisture * (0.10 + 0.90 * litFraction);
    return bow * edge * smoothstep(0.0, 0.10, ray.y) * visibility * 0.16;
}
#endif
