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

// The vanilla celestial sphere turns about world Z once per day: the sun is
// at +X at sunrise, +Y at noon and -X at sunset. Anchoring the galaxy to that
// same rotation makes the band rise from one horizon, cross the sky as one
// continuous sheet and set on the opposite side. The band is not a random
// screen overlay and does not flicker between frames.
float celestialTurn() {
    vec3 sun = normalize(sunDirection());
    return atan(sun.y, sun.x);
}

vec3 turnSky(vec3 v, float angle) {
    float c = cos(angle), s = sin(angle);
    return vec3(c * v.x - s * v.y, s * v.x + c * v.y, v.z);
}

// Galactic frame in the star-fixed reference configuration. The pole is
// tilted about 56 degrees away from the celestial pole, close to the real
// Milky Way's ~60 degree inclination. That tilt is what lets the band sweep
// from a low side arc to a full sheet overhead during the night instead of
// staying in one place.
const float GALAXY_PHASE = 0.85;
const float GALAXY_POLE_X = 0.54;
const float GALAXY_POLE_Y = 0.60;
const float GALAXY_POLE_Z = 0.59;

#if COSMIC_SKY_QUALITY >= 3
#define GALAXY_BAND_OCTAVES 5
#elif COSMIC_SKY_QUALITY >= 2
#define GALAXY_BAND_OCTAVES 4
#else
#define GALAXY_BAND_OCTAVES 3
#endif

// One coherent Milky Way sheet. It follows the real band's large-scale
// structure: a broad, mottled star sheet, a warmer central bulge, dark dust
// lanes and the Great Rift, a few pink H-alpha regions and a faint outer glow.
// Features are anchored in the star frame, so the whole sheet rotates rigidly
// with the night sky. Only analytic noise is used; no textures or tables.
vec3 galaxyNebula(vec3 ray) {
    if (ray.y <= 0.0) return vec3(0.0);
    vec3 sun = normalize(sunDirection());
    // Keep the galaxy out of bright twilight; it develops as the sky darkens.
    float night = smoothstep(0.015, 0.30, -sun.y);
    if (night <= 0.0) return vec3(0.0);

    // Stars are fixed in the rotating frame. Bringing the view ray back into
    // that frame rotates the whole sheet through the sky over the night.
    float turn = celestialTurn() + GALAXY_PHASE;
    vec3 pole = normalize(vec3(GALAXY_POLE_X, GALAXY_POLE_Y, GALAXY_POLE_Z));
    vec3 center = normalize(cross(pole, vec3(0.0, 1.0, 0.0)));
    vec3 starRay = turnSky(ray, -turn);

    // Galactic latitude. Rays far from the plane are rejected before any
    // noise is evaluated, so most of the dome pays only this dot product.
    float lat = dot(starRay, pole);
    if (abs(lat) > 0.50) return vec3(0.0);

    float towardCore = max(dot(starRay, center), 0.0);
    float core = pow(towardCore, 28.0);
    float coreHalo = pow(towardCore, 10.0);

    // Mottled star clouds. A ridged filament term breaks the smooth fbm into
    // the granular, slightly streaky texture seen in wide-field photographs.
    float clouds = skyFbm3(starRay * 7.2, GALAXY_BAND_OCTAVES);
    float filaments = 1.0 - abs(2.0 * skyNoise3(starRay * 18.0) - 1.0);
    float grain = skyNoise3(starRay * 41.0);
    // Slow brightness variation along the band: some stretches are rich star
    // clouds, others are thin between-arm sky.
    float along = smoothstep(0.32, 0.70,
        skyFbm3(starRay * 2.6 + vec3(19.0, 3.0, 8.0), 2));

    // The band edge wanders with the cloud field instead of being a clean
    // mathematical stripe, so the sheet has a ragged real-sky silhouette.
    float width = mix(0.080, 0.128, coreHalo * 0.45);
    width += (clouds - 0.5) * 0.022;
    float sheet = exp(-pow(lat / width, 2.0));
    float spine = exp(-pow(lat / (width * 0.60), 2.0));
    float halo = exp(-pow(lat / 0.40, 2.0)) * 0.075;
    float mosaic = smoothstep(0.30, 0.64, clouds) * (0.62 + 0.38 * filaments);
    mosaic += smoothstep(0.58, 0.88, grain) * 0.22;
    mosaic = clamp(mosaic, 0.0, 1.0);

    // A ragged dust lane sits just off the plane and thickens toward the
    // bulge, matching the visual role of the Great Rift in wide-field photos.
    // The lane absorbs starlight over a broad soft zone rather than drawing a
    // hard black line, and a weaker parallel branch splits it further.
    float dustField = skyFbm3(starRay * 10.0 + vec3(4.7, 9.1, 2.3), 3);
    float warp = (dustField - 0.5) * 0.075;
    float laneCenter = 0.020 + warp;
    float laneWidth = 0.028 + 0.034 * smoothstep(0.26, 0.70, dustField);
    float lane = exp(-pow((lat - laneCenter) / laneWidth, 2.0));
    float rift = lane * (0.38 + 0.62 * dustField) * (0.48 + 0.52 * coreHalo);
    float branch = exp(-pow((lat + 0.078 - warp * 0.7) / 0.040, 2.0)) *
                   smoothstep(0.38, 0.76, dustField) * 0.32;
    float dust = clamp(rift + branch, 0.0, 1.0);

    // Cool blue-white arms, a small warm bulge, sparse rose nebulae. The
    // bulge is kept narrow and close to white; wide amber haze reads as a
    // painted cloud rather than a galaxy.
    vec3 armColor = vec3(0.42, 0.50, 0.68);
    vec3 bulgeColor = vec3(0.79, 0.73, 0.62);
    vec3 color = mix(armColor, bulgeColor, smoothstep(0.06, 0.85, core) * 0.75);
    float nebula = smoothstep(0.62, 0.90, skyNoise3(starRay * 21.0 + 11.0)) *
                   sheet * (0.35 + 0.65 * coreHalo);
    color = mix(color, vec3(0.58, 0.24, 0.34), nebula * 0.42);

    // The bulge is not a smooth glow: its light follows the same star clouds,
    // which keeps the warm centre granular instead of a painted beige blob.
    float coreCloud = mix(0.45, 1.0, mosaic);
    float light = (sheet * (0.26 + 0.74 * mosaic) + spine * 0.12 + halo) *
                  (0.58 + 0.62 * coreHalo * coreCloud);
    light *= 0.78 + 0.44 * along;
    // Dust is brown absorption, not a black hole in the sheet.
    color = mix(color, color * vec3(0.38, 0.32, 0.27), dust * 0.9);
    light *= 1.0 - dust * 0.60;

#if COSMIC_SKY_QUALITY >= 2
    // Unresolved star sparkle plus a dense sub-pixel star layer confined to
    // the band, both anchored in the star frame.
    float sparkle = pow(smoothstep(0.74, 0.97, grain), 2.0);
    color += vec3(0.55, 0.64, 0.86) * sparkle * sheet * 0.22;
    vec2 starUV = vec2(atan(starRay.z, starRay.x),
                       asin(clamp(starRay.y, -1.0, 1.0))) * vec2(820.0, 1080.0);
    float starSeed = hash12(floor(starUV));
    float starPoint = step(0.9982, starSeed) *
                      pow(max(1.0 - length(fract(starUV) - 0.5) * 2.0, 0.0), 7.0);
    vec3 starColor = mix(vec3(0.78, 0.82, 0.92), vec3(0.95, 0.88, 0.74),
                         hash12(floor(starUV) + 5.3));
    color += starColor * starPoint * sheet * 1.15;
#endif

    // Atmospheric extinction near the horizon: the band fades into haze while
    // remaining one sheet, so it visibly rises from one side after dusk. The
    // 1.6 calibration makes the sheet readable at the default 0.25 slider
    // without brightening the independent aurora and event layers.
    return color * light * smoothstep(0.0, 0.16, ray.y) * night * 1.6;
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
