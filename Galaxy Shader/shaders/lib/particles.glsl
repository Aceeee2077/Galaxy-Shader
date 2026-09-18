#ifndef SE_PARTICLES
#define SE_PARTICLES
#include "/lib/noise.glsl"
#include "/lib/weather.glsl"
#include "/lib/seasons.glsl"
#include "/lib/biome.glsl"

float particleNoise3(vec3 p) {
    return (valueNoise(p.xy) + valueNoise(p.yz + 17.3) + valueNoise(p.zx + 31.7)) / 3.0;
}

// Procedural airborne particles. They are evaluated as a sparse world-space
// field so no real Minecraft entities are spawned: pollen and desert dust by
// day, fireflies by night, snow and hail in storms, embers in the Nether and
// cosmic motes in the End.
vec3 particleLayer(vec3 world, float viewDistance) {
    vec3 result = vec3(0.0);
#if PARTICLE_LAYER > 0
    float day = dayAmount();
    float rain = weatherRainAmount();
    float storm = weatherStormAmount();
    float overcast = weatherOvercastAmount();
    vec4 sw = seasonWeights();
    vec2 wind = weatherWindDirection();
    float windStrength = 0.35 + WIND_STRENGTH * 0.6 + storm * 0.8;

    float pollen = 0.0, firefly = 0.0, dust = 0.0, snow = 0.0, hail = 0.0, ember = 0.0, cosmic = 0.0;
#if DIMENSION == -1
    ember = 1.0;
#elif DIMENSION == 1
    cosmic = float(END_PLANETS);
#else
    float cold = biomeCold();
    float coldExtreme = smoothstep(0.75, 0.98, cold);
    float snowBiome = float(biome_precipitation == 2);
    float desert = biomeDesert();
    float humid = sat(biomeJungle() + biomeSwamp());
    pollen = day * (1.0 - rain) * (1.0 - desert) * max(sw.x, sw.y) * 0.9;
    firefly = (1.0 - day) * (1.0 - rain * 0.9) * max(sw.y, sw.z) *
              (0.25 + humid) * (0.35 + 0.65 * biomeHeat());
    dust = day * desert * (0.25 + 0.75 * storm + 0.35 * overcast) * (1.0 - rain * 0.5);
    snow = (snowBiome + coldExtreme * max(sw.w, 0.0) * 0.5) * (rain * 0.7 + storm * 0.5);
    hail = storm * (1.0 - max(snowBiome, coldExtreme)) * (1.0 - desert) * 0.25;
#endif

    float total = pollen + firefly + dust + snow + hail + ember + cosmic;
    if (total <= 0.001) return result;

    vec3 color = vec3(0.90, 0.88, 0.78) * pollen
               + vec3(0.95, 1.00, 0.35) * firefly
               + vec3(0.85, 0.62, 0.35) * dust
               + vec3(0.90, 0.95, 1.00) * snow
               + vec3(0.95, 0.98, 1.00) * hail * 1.4
               + vec3(1.00, 0.40, 0.10) * ember
               + vec3(0.55, 0.65, 1.00) * cosmic * 0.8;
    color /= max(total, 0.001);

    float scale = PARTICLE_LAYER == 1 ? 0.55 : 0.95;
    float driftTime = frameTimeCounter;
#if DIMENSION == 1
    // Match the End orbit clock so zero speed freezes the motes and all
    // supported speeds agree at the 3600 s reset.
    driftTime = fract(frameTimeCounter * (END_ORBIT_SPEED / 900.0)) * 900.0;
#endif
    vec3 drift = vec3(wind.x, 0.0, wind.y) * windStrength * driftTime * 0.35;
    drift.y += ember > 0.0 ? driftTime * 0.60 : -driftTime * 0.20;
    vec3 p = world * scale + drift;
    float n = particleNoise3(p) * 0.70 + particleNoise3(p * 2.7 + vec3(4.1)) * 0.30;
    float threshold = PARTICLE_LAYER == 1 ? 0.70 : 0.62;
    float speck = pow(smoothstep(threshold, 0.98, n), 2.5);
    float distanceFade = exp(-viewDistance * 0.045);
    result = color * speck * total * distanceFade * (PARTICLE_LAYER == 1 ? 0.07 : 0.12);
#endif
    return result;
}

#endif
