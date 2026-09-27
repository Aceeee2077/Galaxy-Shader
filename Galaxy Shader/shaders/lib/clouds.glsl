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
    return 185.0 + weatherOvercastAmount()*70.0 + weatherStormAmount()*95.0;
}

// Weather banks locate the clouds; three-dimensional billows carve their
// interior and silhouette. Stratus and cirrus retain soft vertical profiles.
// "detail" is a per-sample level of detail: distant samples keep the broad
// billow shape but replace the finest octaves and the erosion pass by their
// mean, which is invisible once the far field fades into the atmosphere and
// roughly halves the noise cost of the far half of the march.
float cloudDensity3D(vec3 p, bool lightSample, float detail) {
    float bottom = cloudBottomHeight();
    float thickness = max(cloudThickness(), 1.0);
    float h = (p.y - bottom) / thickness;
    if(h<=0.0 || h>=1.0) return 0.0;
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
    vec2 scale = vec2(0.0024) * wCum + vec2(0.00090) * wStrat +
                 vec2(0.00180, 0.00075) * wCirrus + vec2(0.00120) * wAnvil;
    vec2 uv = p.xz * scale + vec2(frameTimeCounter * 0.010 * CLOUD_SPEED, 0.0)+vec2(41.7,13.2);
    int octaves = detail>0.5 ? min(CLOUD_QUALITY + 2, 6) : min(CLOUD_QUALITY + 1, 4);
    float base;
#if CLOUD_QUALITY <= 3
    // Light transport integrates a broad footprint: keep the mean of omitted
    // fine octaves, while view rays retain all silhouette and erosion detail.
    if(lightSample) base=fbm(uv,3)+0.5*(0.125-exp2(-float(octaves)));
    else
#endif
    base=fbm(uv,octaves);

    vec3 q=vec3(p.x+frameTimeCounter*2.2*CLOUD_SPEED,p.y*1.25,
                p.z+frameTimeCounter*0.45*CLOUD_SPEED)*0.007;
    // Rounded 3D billows, then finer edge erosion. Broad weather noise chooses
    // the location of cloud banks; it no longer extrudes a flat 2D silhouette.
    float billow=volumeNoise(q)*0.64+volumeNoise(q*2.03+17.1)*0.25;
    // The mean of the smallest octave is 0.5, so a constant keeps the average
    // density while skipping the evaluation entirely.
    if(detail>0.5 && !lightSample) billow+=volumeNoise(q*4.07-9.2)*0.11;
    else billow+=0.055;
    float bank=smoothstep(0.25,0.72,base);
    float threshold=mix(0.62,0.32,coverage);
    float tower=pow(h,1.8)*(0.18-0.06*wAnvil);
    float shape=sat((bank*0.46+billow*0.54-threshold-tower)*5.8);
    float erosion;
    if(detail>0.5 && !lightSample) erosion=volumeNoise(q*8.1)*0.10;
    else erosion=0.05;
    erosion*=1.0-shape;
    shape=sat(shape-erosion);
    float sheet=smoothstep(0.40-coverage*0.24,0.72,base)*vertical;
    return mix(shape*edgeBottom*edgeTop,sheet,wStrat*0.60+wCirrus*0.85);
}

// Cheap forward light march for self-shadowing and sun-facing silver linings.
float cloudLightShadow(vec3 p, float detail) {
#if CLOUD_QUALITY == 2
    int taps = 2;
    float stepSize = 35.0;
#elif CLOUD_QUALITY == 3
    int taps = 2;
    // Two longer light samples replace three short ones: the integrated path
    // length stays close to the previous budget, so the self-shadow term keeps
    // its depth while the density is evaluated a third less often.
    float stepSize = 56.0;
#else
    int taps = 4;
    float stepSize = 26.0;
#endif
    vec3 l = lightDirection();
    float accumulated = 0.0;
    for (int i = 0; i < 4; ++i) {
        if (i >= taps) break;
        float segment=stepSize*(1.0+float(i)*0.8);
        float t=stepSize*(0.5+float(i)+0.4*float(i*i));
        accumulated += cloudDensity3D(p + l * t,true,detail)*segment;
    }
    return exp(-accumulated * 0.035);
}

vec3 volumetricClouds(vec3 sky, vec3 ray, vec3 origin, bool reflection) {
    float bottom = cloudBottomHeight();
    float top = bottom + max(cloudThickness(), 1.0);
    float maxDistance = 9600.0;
    if (abs(ray.y) < 0.0009) return sky;

    float t0 = (bottom - origin.y) / ray.y;
    float t1 = (top - origin.y) / ray.y;
    if (t0 > t1) { float tmp = t0; t0 = t1; t1 = tmp; }
    t0 = max(t0, 0.0);
    // Keep the far fade based on the true layer span, then cap the marched span
    // so near-horizon rays spend their samples in the visible part of the deck.
    float fadeDistance = (t0 + t1) * 0.5;
    t1 = min(t1, maxDistance);
    if (t0 >= t1) return sky;

#if CLOUD_QUALITY == 2
    int steps = 16;
#elif CLOUD_QUALITY == 3
    int steps = 24;
#else
    int steps = 36;
#endif

#if CLOUD_QUALITY <= 3
    // Reflections are filtered by water waves/roughness and use half the view
    // budget. Direct sky keeps its 16/24/36 steps.
    if(reflection) steps=max(steps/2,8);
#endif

    float stepLength = (t1 - t0) / float(steps);
    float transmittance = 1.0;
    vec3 inScatter = vec3(0.0);

    vec3 sun = lightDirection();
    float cosTheta = dot(ray, sun);
    float g = 0.68;
    float phase = (1.0 - g * g) / pow(max(1.0 + g * g - 2.0 * g * cosTheta, 0.09), 1.5);
    phase=0.65+phase*0.22;

    float storm = weatherStormAmount();
    float overcast = weatherOvercastAmount();
    float day = dayAmount();
    vec3 litColor = mix(sunlightColor() * 2.8, vec3(1.15,1.20,1.28), overcast * 0.65);
    litColor = mix(litColor, vec3(0.42,0.46,0.54), storm * 0.75);
    litColor = mix(vec3(0.018,0.026,0.046)*NIGHT_BRIGHTNESS,litColor,day);
    vec3 cloudAmbient=mix(vec3(0.010,0.016,0.026)*NIGHT_BRIGHTNESS,
                         vec3(0.20,0.27,0.38),day)*(1.0-storm*0.65);
    vec3 airColor=atmosphere(ray,false);
    float jitter=hash12(gl_FragCoord.xy);
#if TAA_QUALITY > 0
    jitter=fract(jitter+float(frameCounter%8)*0.61803398875);
#endif

    for (int i = 0; i < 48; ++i) {
        if (i >= steps) break;
        float t = t0 + (float(i) + jitter) * stepLength;
        vec3 p = origin + ray * t;
        // The far part of the march keeps the broad billow shape and drops the
        // finest octave and the erosion pass. The split is a fixed fraction of
        // the sample index, so a given sample never changes level while the
        // camera moves; only samples already far from the eye are coarsened.
        float detail = (float(i) < 0.55 * float(steps) || t < 1400.0) ? 1.0 : 0.0;
        float density = cloudDensity3D(p,false,detail);
        if (density <= 0.002) continue;
        float shadow = cloudLightShadow(p,detail);
        float height=sat((p.y-bottom)/(top-bottom));
        float powder = 1.0 - exp(-density * 3.5);
        // Direct transport plus two broad multiple-scattering approximations.
        // Occluded cores stay grey while thin sun-facing edges remain luminous.
        float multiple=0.22*pow(shadow,0.35)+0.08*pow(shadow,0.12);
        vec3 radiance=litColor*(shadow*phase*(0.65+powder*0.35)+multiple);
        radiance+=cloudAmbient*mix(0.30,1.0,height);
        radiance += lightningBoltPosition.w * vec3(0.50, 0.60, 0.78) *
                    density * (0.30 + 0.70 * storm);
        float sigma = 0.035 * (1.0 + overcast * 0.25);
        float alpha = 1.0 - exp(-sigma * density * stepLength);
        float aerial=1.0-exp(-t*0.00010);
        radiance=mix(radiance,airColor,aerial);
        inScatter += transmittance * radiance * alpha;
        transmittance *= (1.0 - alpha);
        if (transmittance < 0.015) break;
    }

    vec3 cloud = sky * transmittance + inScatter;
    float horizonSoft = 1.0 - smoothstep(0.0, 0.22, abs(ray.y));
    float distanceSoft = smoothstep(1800.0, 8000.0, fadeDistance);
    return mix(cloud, sky, horizonSoft * distanceSoft);
}

#endif

// Single-plane cloud sheet. It costs two density lookups and is shared by the
// lowest cloud profile and by the cheap reflection path, so reflective pixels
// never pay for a second volumetric march.
vec3 cloudSheet(vec3 sky, vec3 ray, vec3 origin) {
#if DIMENSION == 0 && CLOUD_QUALITY > 0
    if (ray.y > 0.004) {
        float t = (280.0 - origin.y) / ray.y;
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
            float alpha = density * smoothstep(0.0, 0.12, ray.y) * exp(-t / 18000.0);
            sky = mix(sky, lit, alpha);
        }
    }
#endif
    return sky;
}

// Cheap reflected sky: analytic atmosphere plus the single cloud sheet. Used by
// water and by glossy surfaces, whose detail comes from their own reflections.
vec3 skyReflection(vec3 ray, vec3 origin) {
    return cloudSheet(atmosphere(ray,false), ray, origin);
}

vec3 skyWithClouds(vec3 ray, vec3 origin, bool disks) {
    vec3 sky = atmosphere(ray, disks);
#if DIMENSION == 0 && CLOUD_QUALITY > 0
#if CLOUD_QUALITY >= 2
    sky = volumetricClouds(sky, ray, origin, !disks);
#else
    // Lightweight single-plane fallback for low profiles.
    sky = cloudSheet(sky, ray, origin);
#endif
#endif
    return sky;
}
#endif
