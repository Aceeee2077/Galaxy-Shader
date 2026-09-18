#ifndef SE_CLOUDS
#define SE_CLOUDS
#include "/lib/cloud_field.glsl"
#include "/lib/atmosphere.glsl"

#if DIMENSION == 0 && CLOUD_QUALITY >= 2

float cloudCoverageAmount() {
    return sat(CLOUD_COVERAGE + weatherOvercastAmount()*0.34 +
               weatherRainAmount()*0.20 + weatherStormAmount()*0.16 +
               (dayVariation() - 0.5) * 0.10 + seasonCoverageBias());
}

float cloudBottomHeight() {
    return 195.0 - weatherStormAmount()*38.0 - weatherRainAmount()*10.0;
}

float cloudThickness() {
    return 120.0 + weatherOvercastAmount()*95.0 + weatherStormAmount()*55.0;
}

// One volumetric density sample. Two soft vertical lobes replace the earlier
// hard band, and the fbm threshold is widened so cloud edges fade instead of
// reading as cut-out patches.
float cloudDensity3D(vec3 p) {
    float bottom = cloudBottomHeight();
    float thickness = max(cloudThickness(), 1.0);
    float h = (p.y - bottom) / thickness;
    float edgeBottom = smoothstep(0.0, 0.10, h);
    float edgeTop = 1.0 - smoothstep(0.88, 1.0, h);
    float lowLobe = exp(-pow((h - 0.34) * 3.6, 2.0));
    float highLobe = exp(-pow((h - 0.76) * 2.8, 2.0)) * 0.55;

#if CLOUD_TYPES == 1
    // Weather and season choose a cloud family: storm anvil, flat stratus,
    // high cirrus, or the default cumulus deck.
    float storm = weatherStormAmount();
    float overcast = weatherOvercastAmount();
    vec4 sw = seasonWeights();
    float wAnvil = storm;
    float wStrat = overcast * (1.0 - storm);
    float wCirrus = (1.0 - overcast) * max(sw.y, sw.w) * 0.55;
    float wCum = max(0.0, 1.0 - wAnvil - wStrat - wCirrus);
    float wSum = max(wAnvil + wStrat + wCirrus + wCum, 1e-4);
    wAnvil /= wSum; wStrat /= wSum; wCirrus /= wSum; wCum /= wSum;
#else
    float wAnvil = 0.0, wStrat = 0.0, wCirrus = 0.0, wCum = 1.0;
#endif

    float cumProfile = edgeBottom * edgeTop * sat(lowLobe * 0.85 + highLobe * 0.45);
    float stratProfile = smoothstep(0.02, 0.18, h) * (1.0 - smoothstep(0.45, 0.72, h));
    float cirrusProfile = smoothstep(0.55, 0.75, h) * (1.0 - smoothstep(0.92, 1.0, h));
    float anvilProfile = smoothstep(0.0, 0.08, h) * (1.0 - smoothstep(0.82, 1.0, h));
    float vertical = cumProfile * wCum + stratProfile * wStrat +
                     cirrusProfile * wCirrus + anvilProfile * wAnvil;
    if (vertical <= 0.0) return 0.0;

    float coverage = cloudCoverageAmount() + 0.05 * wAnvil + 0.03 * wStrat;
    vec2 scale = vec2(0.00135) * wCum + vec2(0.00090) * wStrat +
                 vec2(0.00180, 0.00075) * wCirrus + vec2(0.00120) * wAnvil;
    vec2 uv = p.xz * scale + vec2(frameTimeCounter * 0.010 * CLOUD_SPEED, 0.0);
    int octaves = min(CLOUD_QUALITY + 2, 6);
    float base = fbm(uv, octaves);
    vec2 duv = p.xz * 0.0040 - vec2(0.0, frameTimeCounter * 0.004 * CLOUD_SPEED);
    float detail = fbm(duv, min(octaves, 3));

    float coreLow = mix(0.60, 0.52, wAnvil) - coverage * 0.30;
    float coreHigh = mix(0.92, 0.86, wAnvil) - coverage * 0.30;
    float core = smoothstep(coreLow, coreHigh, base);
    float wisp = smoothstep(0.38 - coverage * 0.22, 0.78 - coverage * 0.22, base) *
                 mix(0.32, 0.55, wCirrus);
    float shape = sat(core + wisp);
    shape = mix(shape, shape * (0.62 + 0.38 * detail), mix(0.50, 0.35, wCirrus));
    return sat(shape * vertical);
}

// Cheap forward light march for self-shadowing and sun-facing silver linings.
float cloudLightShadow(vec3 p) {
#if CLOUD_QUALITY == 2
    int taps = 2;
    float stepSize = 34.0;
#elif CLOUD_QUALITY == 3
    int taps = 3;
    float stepSize = 28.0;
#else
    int taps = 4;
    float stepSize = 24.0;
#endif
    vec3 l = lightDirection();
    float accumulated = 0.0;
    for (int i = 0; i < 4; ++i) {
        if (i >= taps) break;
        float t = (float(i) + 0.5) * stepSize;
        accumulated += cloudDensity3D(p + l * t);
    }
    return exp(-accumulated * 0.55);
}

vec3 volumetricClouds(vec3 sky, vec3 ray, vec3 origin) {
    float bottom = cloudBottomHeight();
    float top = bottom + max(cloudThickness(), 1.0);
    float maxDistance = 22000.0;
    if (abs(ray.y) < 0.0009) return sky;

    float t0 = (bottom - origin.y) / ray.y;
    float t1 = (top - origin.y) / ray.y;
    if (t0 > t1) { float tmp = t0; t0 = t1; t1 = tmp; }
    t0 = max(t0, 0.0);
    t1 = min(t1, maxDistance);
    if (t0 >= t1) return sky;

#if CLOUD_QUALITY == 2
    int steps = 8;
#elif CLOUD_QUALITY == 3
    int steps = 14;
#else
    int steps = 20;
#endif

    float stepLength = (t1 - t0) / float(steps);
    float transmittance = 1.0;
    vec3 inScatter = vec3(0.0);

    vec3 sun = lightDirection();
    float cosTheta = sat(dot(ray, sun));
    float g = 0.72;
    float phase = (1.0 - g * g) / pow(max(1.0 + g * g - 2.0 * g * cosTheta, 0.08), 1.5);

    float storm = weatherStormAmount();
    float overcast = weatherOvercastAmount();
    float day = dayAmount();
    vec3 litColor = mix(sunlightColor() * 1.12, vec3(0.55, 0.60, 0.68), overcast * 0.75);
    litColor = mix(litColor, vec3(0.18, 0.21, 0.26), storm * 0.80);
    litColor *= mix(0.08, 1.0, day);
    vec3 cloudAmbient = atmosphere(ray, false) * 0.16;

    for (int i = 0; i < 20; ++i) {
        if (i >= steps) break;
        float t = t0 + (float(i) + 0.5) * stepLength;
        vec3 p = origin + ray * t;
        float density = cloudDensity3D(p);
        if (density <= 0.002) continue;
        float shadow = cloudLightShadow(p);
        float powder = 1.0 - exp(-density * 1.4);
        float silver = pow(max(1.0 - shadow, 0.0), 1.5) * powder;
        vec3 radiance = litColor * (shadow * (0.55 + 0.45 * powder) + silver * 1.0) * phase;
        radiance += cloudAmbient * density * 0.8;
        radiance += lightningBoltPosition.w * vec3(0.50, 0.60, 0.78) *
                    density * (0.30 + 0.70 * storm);
        float sigma = 0.085 * (1.0 + overcast * 0.25);
        float alpha = 1.0 - exp(-sigma * density * stepLength * 0.12);
        inScatter += transmittance * radiance * alpha;
        transmittance *= (1.0 - alpha);
        if (transmittance < 0.015) break;
    }

    vec3 cloud = sky * transmittance + inScatter;
    float cloudAmount = 1.0 - transmittance;
    float tMid = (t0 + t1) * 0.5;
    float horizonSoft = 1.0 - smoothstep(0.0, 0.22, abs(ray.y));
    float distanceSoft = smoothstep(6000.0, 18000.0, tMid);
    return mix(cloud, sky, (1.0 - cloudAmount) * horizonSoft * distanceSoft * 0.28);
}

#endif

vec3 skyWithClouds(vec3 ray, vec3 origin, bool disks) {
    vec3 sky = atmosphere(ray, disks);
#if DIMENSION == 0 && CLOUD_QUALITY > 0
#if CLOUD_QUALITY >= 2
    sky = volumetricClouds(sky, ray, origin);
#else
    // Lightweight single-plane fallback for low profiles.
    float cloudHeight = 280.0;
    float t = (cloudHeight - origin.y) / (abs(ray.y) < 0.005 ? 0.005 : ray.y);
    if (t > 0.0 && t < 18000.0) {
        vec2 p = origin.xz + ray.xz * t;
        float density = cloudDensity(p);
        float neighbor = cloudDensity(p + sunDirection().xz * 55.0);
        float silver = sat(density - neighbor) * 2.0;
        vec3 lit = mix(vec3(0.028, 0.034, 0.046) * NIGHT_BRIGHTNESS,
                       mix(vec3(0.45), sunlightColor() * 0.85, 0.65), dayAmount());
        float overcast = weatherOvercastAmount();
        vec3 stormCloud = mix(vec3(0.18, 0.22, 0.28), vec3(0.075, 0.090, 0.12), weatherStormAmount());
        lit = mix(lit, stormCloud, overcast * 0.78);
        lit *= (0.70 + 0.4 * silver) * (1.0 - 0.34 * weatherStormAmount());
        lit += lightningBoltPosition.w * vec3(0.58, 0.68, 0.86) *
               density * (0.35 + 0.65 * weatherStormAmount());
        float alpha = density * smoothstep(0.0, 0.12, abs(ray.y)) * exp(-t / 18000.0);
        sky = mix(sky, lit, alpha);
    }
#endif
#endif
    return sky;
}
#endif
