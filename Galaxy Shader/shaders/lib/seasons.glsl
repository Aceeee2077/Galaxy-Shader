#ifndef SE_SEASONS
#define SE_SEASONS

// Calendar-driven season system. The year phase is derived from Iris time
// uniforms, while SEASON_MODE can force a specific season for screenshots or
// themed worlds. Weights are smooth triangular windows over a 4-season wheel.

float seasonDayOfYear() {
    float day = 90.0;
#if defined(IS_IRIS)
    day = mod(float(currentYearTime.x), 31536000.0) / 86400.0;
    if ((currentYearTime.x + currentYearTime.y) <= 0) {
        day = float(currentDate.y * 30 + currentDate.z);
    }
#else
    day = 90.0;
#endif
#if SEASON_MODE == 1
    day = 60.0;
#elif SEASON_MODE == 2
    day = 172.0;
#elif SEASON_MODE == 3
    day = 266.0;
#elif SEASON_MODE == 4
    day = 355.0;
#endif
    return mod(day, 365.0);
}

float seasonPhase() {
    return seasonDayOfYear() / 365.0;
}

// x spring, y summer, z autumn, w winter. The spring window wraps across the
// year boundary so early January blends back into spring rather than snapping.
vec4 seasonWeights() {
    float p = seasonPhase() * 4.0;
    vec4 w;
    w.x = pow(max(0.0, 1.0 - abs(p - 0.0)), 2.0) + pow(max(0.0, 1.0 - abs(p - 4.0)), 2.0);
    w.y = pow(max(0.0, 1.0 - abs(p - 1.0)), 2.0);
    w.z = pow(max(0.0, 1.0 - abs(p - 2.0)), 2.0);
    w.w = pow(max(0.0, 1.0 - abs(p - 3.0)), 2.0);
    return w / max(dot(w, vec4(1.0)), 1e-5);
}

vec3 seasonColor(vec3 spring, vec3 summer, vec3 autumn, vec3 winter) {
    vec4 w = seasonWeights();
    vec3 blended = spring * w.x + summer * w.y + autumn * w.z + winter * w.w;
    return mix(vec3(1.0), blended, sat(SEASON_STRENGTH));
}

vec3 seasonSunTint() {
    return seasonColor(vec3(1.00, 1.01, 0.96), vec3(1.04, 0.97, 0.88),
                       vec3(1.07, 0.90, 0.74), vec3(0.94, 0.98, 1.06));
}

vec3 seasonSkyTint() {
    return seasonColor(vec3(0.97, 1.02, 1.04), vec3(0.99, 1.01, 1.03),
                       vec3(1.03, 0.95, 0.86), vec3(0.92, 0.98, 1.08));
}

vec3 seasonAmbientTint() {
    return seasonColor(vec3(0.95, 1.04, 0.96), vec3(1.02, 1.00, 0.94),
                       vec3(1.05, 0.92, 0.80), vec3(0.90, 0.97, 1.06));
}

vec3 seasonFogTint() {
    return seasonColor(vec3(0.96, 1.02, 1.02), vec3(1.01, 1.00, 0.98),
                       vec3(1.04, 0.94, 0.84), vec3(0.92, 0.98, 1.06));
}

float seasonCoverageBias() {
    vec4 w = seasonWeights();
    float bias = 0.00 * w.x + 0.02 * w.y + 0.06 * w.z + 0.10 * w.w;
    return bias * sat(SEASON_STRENGTH);
}

#endif
