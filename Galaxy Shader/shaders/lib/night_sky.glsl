#ifndef SE_NIGHT_SKY
#define SE_NIGHT_SKY
#include "/lib/noise.glsl"
#include "/lib/weather.glsl"

float skyNoise3(vec3 p) {
    return (valueNoise(p.xy) + valueNoise(p.yz + 17.3) + valueNoise(p.zx + 31.7)) / 3.0;
}

float skyFbm3(vec3 p, int octaves) {
    float sum = 0.0, amplitude = 0.5;
    for (int i = 0; i < 5; ++i) {
        if (i >= octaves) break;
        sum += skyNoise3(p) * amplitude;
        p = p * 2.03 + vec3(13.7, 7.1, 23.3);
        amplitude *= 0.5;
    }
    return sum;
}

// A tilted, patchy Milky Way band with cool dust lanes and a warmer core.
vec3 galaxyNebula(vec3 ray) {
    vec3 axis = normalize(vec3(0.22, 0.90, 0.18));
    float plane = 1.0 - abs(dot(ray, axis));
    float band = smoothstep(0.0, 0.10, plane) * pow(smoothstep(0.0, 0.55, plane), 0.5);
    vec3 p = ray * (3.0 + band * 2.0);
    float field = skyFbm3(p * 3.5, 4);
    float core = smoothstep(0.42, 0.86, field) * band;
    float dust = smoothstep(0.58, 0.28, skyNoise3(p * 6.0 + vec3(3.0)));
    vec3 color = mix(vec3(0.035, 0.045, 0.085), vec3(0.20, 0.16, 0.38), core);
    color += vec3(0.08, 0.13, 0.22) * band * 0.35;
    color += vec3(0.24, 0.20, 0.34) * core * 0.55;
    return color * (1.0 - dust * 0.35);
}

// Layered aurora ribbons with fine vertical folds and a soft lower glow.
vec3 auroraSky(vec3 ray, float night) {
    if (ray.y < 0.0 || ray.y > 0.72 || night <= 0.0) return vec3(0.0);
    float azimuth = atan(ray.x, -ray.z);
    float north = 1.0 - smoothstep(1.10, 2.20, abs(azimuth));
    if (north <= 0.0) return vec3(0.0);
    float time = frameTimeCounter * 0.035;
    float warp = sin(azimuth * 5.0 + time) * 0.043 +
                 sin(azimuth * 11.0 - time * 0.73) * 0.019;
    float folds = 0.58 + 0.42 * pow(0.5 + 0.5 * sin(azimuth * 68.0 +
                   sin(azimuth * 12.0 + time) * 2.0 - time * 1.5), 4.0);
    float lower = exp(-pow((ray.y - 0.19 - warp) / 0.095, 2.0));
    float upper = exp(-pow((ray.y - 0.36 + warp * 0.65) / 0.13, 2.0));
    float veil = (1.0 - smoothstep(0.04, 0.68, ray.y)) *
                 smoothstep(0.0, 0.09, ray.y);
    float variation = 0.68 + 0.32 * skyNoise3(vec3(azimuth * 3.0, ray.y * 7.0, time * 0.2));
    vec3 green = vec3(0.035, 0.47, 0.24) * lower;
    vec3 violet = vec3(0.24, 0.09, 0.38) * upper;
    vec3 cyan = vec3(0.035, 0.17, 0.24) * (lower + upper) * 0.48;
    float strength = COSMIC_SKY_QUALITY == 3 ? 1.0 : 0.78;
    return (green + violet + cyan) * folds * veil * variation * north * night * strength;
}

// Occasional short streaks. Conservative by default: they are bright, brief, and
// deterministic, and never contribute to the vanilla star field.
vec3 shootingStars(vec3 ray) {
    vec3 color = vec3(0.0);
#if COSMIC_SKY_QUALITY >= 2
    for (int i = 0; i < 5; ++i) {
        float fi = float(i);
        float seed = hash12(vec2(fi, 11.0));
        float period = 7.0 + seed * 14.0;
        float cycle = fract((frameTimeCounter * 0.10 + seed * 37.0) / period);
        float life = smoothstep(0.0, 0.08, cycle) * (1.0 - smoothstep(0.08, 0.34, cycle));
        if (life <= 0.0) continue;
        float azimuth = seed * 6.2831853 + frameTimeCounter * 0.0008;
        float elevation = 0.24 + hash12(vec2(fi, 23.0)) * 0.42;
        vec3 head = vec3(cos(azimuth) * cos(elevation), sin(elevation), sin(azimuth) * cos(elevation));
        vec3 tail = normalize(head - vec3(-0.10, -0.26, 0.06) * 0.28);
        float angle = acos(clamp(dot(ray, head), -1.0, 1.0));
        float tailAngle = acos(clamp(dot(ray, tail), -1.0, 1.0));
        float along = sat((angle - tailAngle) / max(0.10, 1.0 - tailAngle));
        float proximity = 1.0 - smoothstep(0.0, 0.016 + along * 0.018, angle);
        color += vec3(0.55, 0.75, 1.0) * proximity * life * (0.45 + 0.55 * along) * 1.35;
    }
#endif
    return color;
}

#endif
