#ifndef SE_ICE_HALO
#define SE_ICE_HALO

// The 22-degree halo family produced by hexagonal ice crystals in cirrus.
// Everything is analytic and angular: one dot product rejects every pixel
// farther than ~35 degrees from the light source, and the parhelia/pillar
// terms add a few trigonometry calls only for a low light source. `lunar`
// keeps the moon dimmer and cool, but it still draws parhelia and a tangent
// arc when the same plate crystals are lit by moonlight.
vec3 iceHalo(vec3 ray, vec3 lightDir, float visibility, vec3 tint, float lunar) {
    if (visibility <= 1e-4) return vec3(0.0);
    float d = dot(ray, lightDir);
    if (d < 0.80) return vec3(0.0);

    const float deg = PI / 180.0;
    float theta = acos(clamp(d, -1.0, 1.0));

    // A sharp inner edge with a longer outer skirt reads as the crystal ring
    // instead of another smooth solar aureole. Red sits on the inner rim and
    // blue on the outside, as in a real 22-degree halo.
    float ringInner = 20.6 * deg;
    float ringPeak = 22.0 * deg;
    float ring = smoothstep(ringInner, ringPeak, theta) *
                 exp(-max(theta - ringPeak, 0.0) / (2.3 * deg));
    vec3 ringColor = mix(vec3(1.0, 0.62, 0.48), vec3(0.58, 0.74, 1.0),
                         smoothstep(ringPeak - 0.7 * deg,
                                    ringPeak + 2.2 * deg, theta));
    vec3 result = ringColor * ring * 0.075;

    if (lunar < 0.5 && lightDir.y > -0.01) {
        float horizontal = max(length(lightDir.xz), 1e-4);
        vec2 heading = lightDir.xz / horizontal;
        float cs = cos(22.0 * deg);
        float sn = sin(22.0 * deg);
        vec2 leftHeading = vec2(heading.x * cs - heading.y * sn,
                                heading.x * sn + heading.y * cs);
        vec2 rightHeading = vec2(heading.x * cs + heading.y * sn,
                                 -heading.x * sn + heading.y * cs);
        vec3 leftDog = vec3(leftHeading.x * horizontal, lightDir.y,
                            leftHeading.y * horizontal);
        vec3 rightDog = vec3(rightHeading.x * horizontal, lightDir.y,
                             rightHeading.y * horizontal);
        float elevation = asin(clamp(ray.y, -1.0, 1.0));

        vec3 sunFlat = normalize(vec3(lightDir.x, 0.0, lightDir.z));
        vec3 sunSide = normalize(cross(vec3(0.0, 1.0, 0.0), sunFlat));
        float azimuthFromSun = atan(dot(ray, sunSide), dot(ray, sunFlat));

        // Sun dogs are bright vertical smears on the ring. Their horizontal
        // angle is wide by about a degree and their vertical extent is several
        // degrees, so each is evaluated in its own azimuth/elevation frame.
        // As the sun drops toward the horizon the smear stretches into a short
        // pillar, because the same plate crystals scatter light over a longer
        // vertical path; the horizontal width stays the same.
        float dogVertical = mix(6.2 * deg, 2.5 * deg,
                                smoothstep(0.02, 0.20, lightDir.y));
        float dog = 0.0;
        for (int i = 0; i < 2; i++) {
            vec3 dogDir = i == 0 ? leftDog : rightDog;
            vec3 dogFlat = normalize(vec3(dogDir.x, 0.0, dogDir.z));
            vec3 dogSide = normalize(cross(vec3(0.0, 1.0, 0.0), dogFlat));
            float azimuth = atan(dot(ray, dogSide), dot(ray, dogFlat));
            float vertical = elevation - asin(clamp(dogDir.y, -1.0, 1.0));
            dog += exp(-pow(azimuth / (1.05 * deg), 2.0)) *
                   exp(-pow(vertical / dogVertical, 2.0));
        }
        float lowSun = smoothstep(0.015, 0.075, lightDir.y) *
                       (1.0 - smoothstep(0.26, 0.42, lightDir.y));
        // Parhelia are small spectra: the flank facing the sun is red-orange
        // and the far flank runs to pale blue. The split uses the ray's
        // distance from the sun's azimuth, so it costs no extra trigonometry.
        float dogSpectral = smoothstep(-0.012, 0.012,
                                       abs(azimuthFromSun) - 22.0 * deg);
        vec3 dogTint = mix(vec3(1.00, 0.56, 0.34), vec3(0.86, 0.90, 1.0),
                           dogSpectral);
        result += dogTint * dog * lowSun * 0.11;

        // Upper tangent arc: a shallow bright band tangent to the top of the
        // ring, strongest straight above the sun.
        float aboveSun = elevation - asin(clamp(lightDir.y, -1.0, 1.0));
        float tangent = exp(-pow(azimuthFromSun / (9.0 * deg), 2.0)) *
                        smoothstep(19.0 * deg, 21.5 * deg, aboveSun) *
                        (1.0 - smoothstep(28.0 * deg, 33.0 * deg, aboveSun)) *
                        smoothstep(18.0 * deg, 20.5 * deg, theta) *
                        (1.0 - smoothstep(26.0 * deg, 29.0 * deg, theta));
        result += vec3(0.85, 0.90, 1.0) * tangent * 0.045;

        // Lower tangent arc: the mirror of the upper cap, seen once the sun
        // climbs above roughly 32 degrees. It hugs the bottom of the ring and
        // is brightest straight below the sun, fading out to the sides.
        float higherSun = smoothstep(0.52, 0.62, lightDir.y);
        if (higherSun > 0.0) {
            float belowSun = asin(clamp(lightDir.y, -1.0, 1.0)) - elevation;
            float lowerTangent = exp(-pow(azimuthFromSun / (12.0 * deg), 2.0)) *
                                 smoothstep(19.5 * deg, 22.0 * deg, belowSun) *
                                 (1.0 - smoothstep(27.0 * deg, 32.0 * deg, belowSun)) *
                                 smoothstep(18.0 * deg, 20.5 * deg, theta) *
                                 (1.0 - smoothstep(26.0 * deg, 29.0 * deg, theta));
            result += vec3(0.86, 0.90, 1.0) * lowerTangent * higherSun * 0.040;
        }

        // Sun pillar: a vertical shaft of light above (and faintly below) a
        // low sun. It is narrow in azimuth and fades over roughly 15 degrees.
        float pillarGate = smoothstep(-0.005, 0.035, lightDir.y) *
                           (1.0 - smoothstep(0.20, 0.34, lightDir.y));
        float pillar = exp(-pow(azimuthFromSun / (1.5 * deg), 2.0));
        if (aboveSun >= 0.0) {
            pillar *= exp(-aboveSun / (8.0 * deg)) *
                      (1.0 - smoothstep(13.0 * deg, 20.0 * deg, aboveSun));
        } else {
            pillar *= exp(aboveSun / (3.0 * deg)) * 0.30;
        }
        result += tint * pillar * pillarGate * smoothstep(0.0, 0.02, ray.y) * 0.10;
    } else if (lunar > 0.5 && lightDir.y > -0.01) {
        // A bright moon also draws a narrow pillar from the same plate
        // crystals. It is dimmer and cooler than the solar shaft.
        vec3 moonFlat = normalize(vec3(lightDir.x, 0.0, lightDir.z));
        vec3 moonSide = normalize(cross(vec3(0.0, 1.0, 0.0), moonFlat));
        float moonAzimuth = atan(dot(ray, moonSide), dot(ray, moonFlat));
        float elevation = asin(clamp(ray.y, -1.0, 1.0));
        float aboveMoon = elevation - asin(clamp(lightDir.y, -1.0, 1.0));
        float pillarGate = smoothstep(-0.005, 0.035, lightDir.y) *
                           (1.0 - smoothstep(0.20, 0.34, lightDir.y));
        float pillar = exp(-pow(moonAzimuth / (1.8 * deg), 2.0));
        if (aboveMoon >= 0.0) {
            pillar *= exp(-aboveMoon / (8.0 * deg)) *
                      (1.0 - smoothstep(13.0 * deg, 20.0 * deg, aboveMoon));
        } else {
            pillar *= exp(aboveMoon / (3.0 * deg)) * 0.25;
        }
        result += vec3(0.72, 0.80, 1.0) * pillar * pillarGate *
                  smoothstep(0.0, 0.02, ray.y) * 0.055;

        // Moon dogs: the same 22-degree parhelia, much fainter and cool. They
        // still need a low moon because the plate crystals must be near
        // horizontal to split the moonlight sideways.
        float lunarDogGate = smoothstep(0.015, 0.070, lightDir.y) *
                             (1.0 - smoothstep(0.24, 0.40, lightDir.y));
        if (lunarDogGate > 0.0) {
            float horizontal = max(length(lightDir.xz), 1e-4);
            vec2 heading = lightDir.xz / horizontal;
            float cs = cos(22.0 * deg);
            float sn = sin(22.0 * deg);
            vec2 leftHeading = vec2(heading.x * cs - heading.y * sn,
                                    heading.x * sn + heading.y * cs);
            vec2 rightHeading = vec2(heading.x * cs + heading.y * sn,
                                     -heading.x * sn + heading.y * cs);
            float dog = 0.0;
            for (int i = 0; i < 2; i++) {
                vec2 dogHeading = i == 0 ? leftHeading : rightHeading;
                vec3 dogDir = vec3(dogHeading.x * horizontal, lightDir.y,
                                   dogHeading.y * horizontal);
                vec3 dogFlat = normalize(vec3(dogDir.x, 0.0, dogDir.z));
                vec3 dogSide = normalize(cross(vec3(0.0, 1.0, 0.0), dogFlat));
                float azimuth = atan(dot(ray, dogSide), dot(ray, dogFlat));
                float vertical = elevation - asin(clamp(dogDir.y, -1.0, 1.0));
                dog += exp(-pow(azimuth / (1.15 * deg), 2.0)) *
                       exp(-pow(vertical / (2.8 * deg), 2.0));
            }
            result += vec3(0.76, 0.84, 1.0) * dog * lunarDogGate * 0.070;

            // Lunar upper tangent arc: a pale cap tangent to the top of the
            // ring, narrower and weaker than its solar counterpart.
            float tangent = exp(-pow(moonAzimuth / (10.0 * deg), 2.0)) *
                            smoothstep(19.5 * deg, 21.8 * deg, aboveMoon) *
                            (1.0 - smoothstep(27.0 * deg, 32.0 * deg, aboveMoon)) *
                            smoothstep(18.0 * deg, 20.5 * deg, theta) *
                            (1.0 - smoothstep(26.0 * deg, 29.0 * deg, theta));
            result += vec3(0.72, 0.80, 1.0) * tangent * lunarDogGate * 0.028;
        }
    }

    return result * visibility;
}
#endif
