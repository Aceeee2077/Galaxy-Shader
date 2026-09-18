#ifndef SE_CAUSTICS
#define SE_CAUSTICS
#include "/lib/noise.glsl"

// Ridged fbm veins used for underwater caustics. Two offset layers keep the
// pattern from reading as a single repeating texture.
float causticField(vec2 p) {
    float n = valueNoise(p)
            + 0.50 * valueNoise(p * 2.13 + vec2(3.7, 1.9))
            + 0.25 * valueNoise(p * 4.21 + vec2(9.1, 4.3));
    n /= 1.75;
    float ridge = 1.0 - abs(n * 2.0 - 1.0);
    return pow(sat(ridge), 3.0);
}

#endif
