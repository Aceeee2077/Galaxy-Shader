#ifndef SE_WEATHER
#define SE_WEATHER
#include "/lib/noise.glsl"

float weatherRainAmount() {
    return sat(rainStrength * RAIN_INTENSITY);
}

float weatherStormAmount() {
    return sat(max(thunderStrength, rainStrength * thunderStrength));
}

// Wetness is supplied by Iris with slow drying, while rainStrength handles the
// immediate storm transition. Their union avoids visual popping at either edge.
float weatherWetness() {
    return sat(max(wetness, weatherRainAmount() * 0.72));
}

float weatherOvercastAmount() {
    float manualClouds = smoothstep(0.38, 0.66, CLOUD_COVERAGE);
    return sat(max(weatherRainAmount() * 0.84, weatherWetness() * 0.38) +
               manualClouds * 0.42 + weatherStormAmount() * 0.18);
}

float dawnDuskAmount() {
    float sunHeight = sunDirection().y;
    return (1.0 - smoothstep(0.20, 0.55, abs(sunHeight))) *
           smoothstep(-0.10, 0.045, sunHeight);
}

vec2 weatherWindDirection() {
    vec2 direction = vec2(0.84, 0.38);
    float turn = valueNoise(vec2(frameTimeCounter * 0.015, 17.0)) - 0.5;
    float angle = turn * (0.35 + weatherStormAmount() * 0.55);
    return mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * direction;
}

// Procedural impact field shared by water and exposed terrain. Each world-space
// cell owns one ring whose phase is hashed, expands, then fades before respawn.
// xy is the radial normal gradient; z is the narrow splash crest.
vec3 rainRippleField(vec2 world, float scaleBias) {
    vec2 gradient = vec2(0.0);
    float crest = 0.0;
#if WEATHER_QUALITY > 0
    int layerCount = WEATHER_QUALITY;
    for (int i = 0; i < 4; ++i) {
        if (i >= layerCount) break;
        float fi = float(i);
        float scale = scaleBias * (0.72 + fi * 0.31);
        vec2 gridPosition = world * scale + vec2(fi * 19.7, fi * 7.3);
        vec2 cell = floor(gridPosition);
        float seed = hash12(cell + fi * 31.0);
        vec2 center = vec2(hash12(cell + 4.7), hash12(cell + 13.1)) * 0.62 + 0.19;
        vec2 local = fract(gridPosition) - center;
        float age = fract(frameTimeCounter * (0.72 + fi * 0.11) + seed);
        float radius = age * 0.62;
        float distanceToRing = length(local);
        float width = mix(0.042, 0.018, age);
        float ring = exp(-pow((distanceToRing - radius) / max(width, 0.008), 2.0));
        float life = pow(sin(PI * age), 2.0);
        vec2 radial = local / max(distanceToRing, 0.002);
        gradient += radial * ring * life * (1.0 - age) / (1.0 + fi * 0.45);
        crest += ring * life * smoothstep(0.0, 0.12, age) / (1.0 + fi);
    }
#endif
    return vec3(gradient, crest);
}

#endif
