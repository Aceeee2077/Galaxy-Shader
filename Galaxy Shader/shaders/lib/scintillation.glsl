#ifndef SE_SCINTILLATION
#define SE_SCINTILLATION

// Turbulence in the lower atmosphere bends a star's light many times a second.
// The result is a fast, irregular flicker that is strongest near the horizon,
// where the line of sight crosses the most air. Each star gets its own phase and
// rate from a stable hash, so the pattern is deterministic without any texture.
float starScintillation(float seed, float altitude, float time, float amount) {
    if (amount <= 0.0) return 1.0;
    float airMass = mix(2.2, 1.0, smoothstep(0.03, 0.60, altitude));
    float speed = 6.0 + 10.0 * seed;
    float phase = seed * 37.0;
    float wobble = 0.55 * sin(time * speed + phase) +
                   0.30 * sin(time * speed * 2.3 + phase * 1.7) +
                   0.15 * sin(time * speed * 4.1 + phase * 0.6);
    return max(1.0 + amount * airMass * 0.45 * wobble, 0.08);
}
#endif
