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

    // Faint 46-degree ring, red on the inner edge and blue outside.
    float angle = acos(clamp(dot(ray, sun), -1.0, 1.0));
    float offset = angle - ring;
    float band = exp(-pow(offset / 0.020, 2.0));
    vec3 ringTint = mix(vec3(1.0, 0.58, 0.46), vec3(0.56, 0.70, 1.0),
                        smoothstep(-0.02, 0.02, offset));
    colour += ringTint * band * 0.038 * visibility;

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

    // Parhelic circle: a white horizontal band crossing the sky at the sun's
    // altitude. Plate crystals spread it all the way around, with a bright
    // patch near the sun and a second one around the 120-degree parhelia.
    if (sun.y > 0.02) {
        float height = exp(-pow((ray.y - sun.y) / 0.009, 2.0));
        if (height > 0.01) {
            vec3 flatSun = vec3(sun.x, 0.0, sun.z);
            flatSun = length(flatSun) > 1e-4 ? normalize(flatSun) : vec3(0.0, 0.0, 1.0);
            vec3 flatRay = vec3(ray.x, 0.0, ray.z);
            float azimuth = length(flatRay) > 1e-4 ?
                dot(normalize(flatRay), flatSun) : 1.0;
            float nearSun = pow(max(azimuth, 0.0), 3.0);
            float parhelia = exp(-pow((acos(clamp(azimuth, -1.0, 1.0)) - 2.094) / 0.30, 2.0));
            float strength = 0.35 + 0.65 * nearSun + 0.45 * parhelia;
            colour += vec3(0.86, 0.89, 0.96) * height * strength * visibility * 0.030;
        }
    }
    return colour;
}
#endif
