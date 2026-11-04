#ifndef SE_ICE_HALO_EXTRAS
#define SE_ICE_HALO_EXTRAS

// Two faint companions of the 22-degree halo family. The 46-degree ring is the
// second ice-crystal halo and stays pale and broad. When the sun climbs above
// about 58 degrees, plate crystals instead light the circumhorizontal arc: a
// horizontal spectral band roughly 46 degrees below the sun. Both are analytic
// angle terms; the ring exits after the half-space dot with the sun, and the
// arc exits before any trigonometry unless the sun is high.
vec3 iceHaloCompanions(vec3 ray, vec3 sun, float visibility) {
    if (visibility <= 0.0 || ray.y <= 0.0) return vec3(0.0);

    const float ring = 0.80285; // 46 degrees
    vec3 colour = vec3(0.0);

    // Faint 46-degree ring, red on the inner edge and blue outside. The band
    // is a 0.02-radian Gaussian: nine degrees off the ring it underflows to
    // float zero, so a pair of dot-product bounds skips the acos and exp for
    // almost every sky pixel while keeping the ring itself unchanged.
    float ringDot = dot(ray, sun);
    if (ringDot > 0.574 && ringDot < 0.799) {
        float angle = acos(clamp(ringDot, -1.0, 1.0));
        float offset = angle - ring;
        float band = exp(-pow(offset / 0.020, 2.0));
        vec3 ringTint = mix(vec3(1.0, 0.58, 0.46), vec3(0.56, 0.70, 1.0),
                            smoothstep(-0.02, 0.02, offset));
        colour += ringTint * band * 0.038 * visibility;
    }

    // Circumhorizontal arc: only with a high sun, a horizontal band 46 degrees
    // below it. Red sits on the upper edge, blue-violet below.
    float highSun = smoothstep(0.98, 1.10, asin(clamp(sun.y, -1.0, 1.0)));
    if (highSun > 0.0) {
        vec3 flatSun = vec3(sun.x, 0.0, sun.z);
        flatSun = length(flatSun) > 1e-4 ? normalize(flatSun) : vec3(0.0, 0.0, 1.0);
        vec3 flatRay = vec3(ray.x, 0.0, ray.z);
        float azimuth = length(flatRay) > 1e-4 ?
            dot(normalize(flatRay), flatSun) : 1.0;
        float around = smoothstep(0.24, 0.62, azimuth);
        float target = asin(clamp(sun.y, -1.0, 1.0)) - ring;
        float elevation = asin(clamp(ray.y, -1.0, 1.0));
        float vertical = elevation - target;
        float arc = exp(-pow(vertical / 0.024, 2.0)) *
                    (1.0 - smoothstep(0.060, 0.095, abs(vertical)));
        vec3 arcTint = mix(vec3(0.25, 0.35, 1.0), vec3(1.0, 0.30, 0.12),
                           smoothstep(-0.010, 0.010, vertical));
        colour += arcTint * arc * around * highSun * visibility * 0.18;
    }

    // Circumzenithal arc: the high, sunward smile of plate crystals, about 46
    // degrees above the sun, gone before the sun reaches 30 degrees. Red sits
    // on its lower edge and violet on the upper edge.
    float sunElevation = asin(clamp(sun.y, -1.0, 1.0));
    float lowSun = smoothstep(0.015, 0.060, sunElevation) *
                   (1.0 - smoothstep(0.38, 0.46, sunElevation));
    if (lowSun > 0.0) {
        vec3 flatSun = vec3(sun.x, 0.0, sun.z);
        flatSun = length(flatSun) > 1e-4 ? normalize(flatSun) : vec3(0.0, 0.0, 1.0);
        vec3 flatRay = vec3(ray.x, 0.0, ray.z);
        float azimuth = length(flatRay) > 1e-4 ?
            dot(normalize(flatRay), flatSun) : 1.0;
        // The arc fades to zero more than 60 degrees off the sun's azimuth, so
        // rays outside that cone skip the acos and everything that follows.
        if (azimuth > 0.48) {
            float angle = acos(clamp(azimuth, -1.0, 1.0));
            float around = 1.0 - smoothstep(0.55, 1.05, angle);
            // The ends of the arc sag toward the horizon, giving the familiar
            // smile.
            float target = sunElevation + ring - 0.14 * angle * angle;
            float elevation = asin(clamp(ray.y, -1.0, 1.0));
            float vertical = elevation - target;
            float arc = exp(-pow(vertical / 0.022, 2.0)) *
                        (1.0 - smoothstep(0.050, 0.080, abs(vertical)));
            vec3 arcTint = mix(vec3(1.0, 0.30, 0.12), vec3(0.28, 0.32, 1.0),
                               smoothstep(-0.010, 0.010, vertical));
            colour += arcTint * arc * around * lowSun * visibility * 0.22;
        }
    }

    // Upper Parry arc: a thin chevron riding above the top of the 22-degree
    // halo when the sun sits between roughly 13 and 32 degrees. It needs
    // vertically aligned plate crystals, so it is rarer and fainter than the
    // tangent arc; the ends of the bow sag toward the ring, giving the
    // sun-cave shape instead of a second tangent cap.
    float parrySun = smoothstep(0.22, 0.28, sunElevation) *
                     (1.0 - smoothstep(0.50, 0.57, sunElevation));
    if (parrySun > 0.0) {
        vec3 flatSun = vec3(sun.x, 0.0, sun.z);
        flatSun = length(flatSun) > 1e-4 ? normalize(flatSun) : vec3(0.0, 0.0, 1.0);
        vec3 flatRay = vec3(ray.x, 0.0, ray.z);
        float azimuth = length(flatRay) > 1e-4 ?
            dot(normalize(flatRay), flatSun) : 1.0;
        // The bow is gone beyond 30 degrees of azimuth; reject it with the dot
        // before paying for the acos, which is most of the sky.
        if (azimuth > 0.865) {
            float side = acos(clamp(azimuth, -1.0, 1.0));
            float spread = 1.0 - smoothstep(0.40, 0.52, side);
            if (spread > 0.0) {
                // The bow peaks 25 degrees above the sun and bends down to
                // the ring at 21.5 degrees by the time it runs 25 degrees
                // sideways.
                float u = min(side / 0.44, 1.0);
                float target = 0.44 - 0.065 * u * u;
                float vertical = asin(clamp(ray.y, -1.0, 1.0)) -
                                 sunElevation - target;
                float band = exp(-pow(vertical / 0.014, 2.0)) *
                             (1.0 - smoothstep(0.030, 0.045, abs(vertical)));
                // Red inner edge, near-white body, violet outer edge: a thin
                // spectral rim on either side of a mostly uncoloured band.
                vec3 arcTint = mix(vec3(1.0, 0.42, 0.20),
                                   vec3(1.0, 0.95, 0.86),
                                   smoothstep(-0.009, -0.001, vertical));
                arcTint = mix(arcTint, vec3(0.52, 0.60, 1.0),
                              smoothstep(0.001, 0.009, vertical));
                colour += arcTint * band * spread * parrySun * visibility * 0.060;
            }
        }
    }

    // Parhelic circle: a white horizontal band crossing the sky at the sun's
    // altitude. Plate crystals spread it all the way around, with a bright
    // patch near the sun and a second one around the 120-degree parhelia.
    // The band is a 0.009-radian (half-degree) Gaussian; about 0.15 radians
    // away the exponent falls below -277 and `exp` underflows to float zero,
    // so a vertical bound skips the call for most of the sky.
    if (sun.y > 0.02 && abs(ray.y - sun.y) < 0.15) {
        float height = exp(-pow((ray.y - sun.y) / 0.009, 2.0));
        if (height > 0.01) {
            vec3 flatSun = vec3(sun.x, 0.0, sun.z);
            flatSun = length(flatSun) > 1e-4 ? normalize(flatSun) : vec3(0.0, 0.0, 1.0);
            vec3 flatRay = vec3(ray.x, 0.0, ray.z);
            float azimuth = length(flatRay) > 1e-4 ?
                dot(normalize(flatRay), flatSun) : 1.0;
            float nearSun = pow(max(azimuth, 0.0), 3.0);
            float parhelia = exp(-pow((acos(clamp(azimuth, -1.0, 1.0)) - 2.094) / 0.30, 2.0));
            // Anthelion: the band's faint 180-degree counterpart to the bright
            // patch near the sun. `azimuth` is already the cosine to the sun,
            // so the spot needs no new trigonometry: a high power of the
            // anti-solar cosine gives a soft spot roughly 20 degrees across.
            float anthelion = pow(max(-azimuth, 0.0), 48.0);
            float strength = 0.35 + 0.65 * nearSun + 0.45 * parhelia +
                             0.34 * anthelion;
            colour += vec3(0.86, 0.89, 0.96) * height * strength * visibility * 0.030;
        }
    }
    return colour;
}
#endif
