#ifndef SE_CELESTIAL
#define SE_CELESTIAL
#include "/lib/noise.glsl"
#include "/lib/seasons.glsl"

float celestialNoise3(vec3 p) {
    return (valueNoise(p.xy) + valueNoise(p.yz + 17.3) + valueNoise(p.zx + 31.7)) / 3.0;
}

// Event schedule. Normal mode follows the calendar year; frequent mode
// compresses the same wheel four times so events can be seen without waiting
// months of real time.
float celestialDay() {
    float day = seasonDayOfYear();
#if CELESTIAL_EVENTS == 2
    day = mod(day * 4.0, 365.0);
#endif
    return day;
}

float celestialWindow(float day, float center, float halfWidth) {
    float delta = abs(mod(day - center + 182.5, 365.0) - 182.5);
    return 1.0 - smoothstep(halfWidth * 0.5, halfWidth, delta);
}

#if CELESTIAL_EVENTS == 0
float celestialScale() { return 0.0; }
#else
float celestialScale() { return 1.0; }
#endif

float meteorShowerAmount() {
    float day = celestialDay();
    float amount = max(celestialWindow(day, 200.0, 8.0), celestialWindow(day, 310.0, 6.0));
    return amount * celestialScale();
}

float auroraStormAmount() {
    float day = celestialDay();
    float amount = max(celestialWindow(day, 80.0, 6.0), celestialWindow(day, 266.0, 6.0));
    return amount * celestialScale();
}

float cometAmount() {
    return celestialWindow(celestialDay(), 120.0, 12.0) * celestialScale();
}

float supernovaAmount() {
    return celestialWindow(celestialDay(), 355.0, 1.5) * celestialScale();
}

// Solar eclipse: one short window near noon on a specific calendar day.
// worldTime is 0 at sunrise and 6000 at noon in the vanilla day cycle.
float eclipseAmount() {
    float window = celestialWindow(celestialDay(), 172.0, 1.0) * celestialScale();
    if (window <= 0.0) return 0.0;
    float delta = abs(mod(float(worldTime) - 6000.0 + 12000.0, 24000.0) - 12000.0);
    return window * (1.0 - smoothstep(120.0, 420.0, delta));
}

// A comet head with a short dust tail, fixed in direction space.
vec3 cometSky(vec3 ray, float night) {
    float amount = cometAmount();
    if (amount <= 0.0 || night <= 0.0) return vec3(0.0);
    vec3 head = normalize(vec3(-0.35, 0.30, -0.88));
    vec3 tailDir = normalize(vec3(0.30, -0.55, 0.35));
    float headGlow = pow(sat(dot(ray, head)), 900.0);
    float tail = 0.0;
    for (int i = 0; i < 6; ++i) {
        float t = float(i) / 5.0;
        vec3 p = normalize(head + tailDir * t * 0.55);
        float d = acos(clamp(dot(ray, p), -1.0, 1.0));
        tail += (1.0 - smoothstep(0.0, 0.045 + t * 0.05, d)) * (1.0 - t);
    }
    float dust = 0.55 + 0.45 * celestialNoise3(ray * 22.0);
    return (vec3(0.55, 0.72, 1.0) * headGlow * 1.6 +
            vec3(0.35, 0.55, 0.85) * tail * 0.35 * dust) * amount * night;
}

// A rare supernova flash: bright core plus a soft colour halo.
vec3 supernovaSky(vec3 ray, float night) {
    float amount = supernovaAmount();
    if (amount <= 0.0 || night <= 0.0) return vec3(0.0);
    vec3 dir = normalize(vec3(0.62, 0.42, 0.66));
    float d = acos(clamp(dot(ray, dir), -1.0, 1.0));
    float core = 1.0 - smoothstep(0.0, 0.006, d);
    float halo = exp(-d * 36.0);
    return (vec3(0.85, 0.90, 1.0) * core * 2.2 +
            vec3(0.45, 0.35, 0.75) * halo * 0.5) * amount * night;
}

#endif
