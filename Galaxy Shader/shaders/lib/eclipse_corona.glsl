#ifndef SE_ECLIPSE_CORONA
#define SE_ECLIPSE_CORONA

// During totality the Moon hides the solar photosphere and the hot corona
// becomes visible as pale streamers and polar plumes, with a few red
// prominences on the limb. Everything is analytic, confined to a small cone
// around the Sun and exits after one dot product.
vec3 eclipseCorona(vec3 ray, vec3 sunDir, float eclipse, float time) {
    if (eclipse <= 0.0) return vec3(0.0);
    float cosA = dot(ray, sunDir);
    if (cosA < 0.94) return vec3(0.0); // about 20 degrees
    const float deg = PI / 180.0;
    float r = acos(clamp(cosA, -1.0, 1.0));
    if (r < 0.55 * deg) return vec3(0.0);

    vec3 ref = abs(sunDir.y) < 0.95 ? vec3(0.0, 1.0, 0.0)
                                    : vec3(1.0, 0.0, 0.0);
    vec3 east = normalize(cross(ref, sunDir));
    vec3 north = cross(sunDir, east);
    vec3 tangent = normalize(ray - sunDir * cosA);
    float azimuth = atan(dot(tangent, north), dot(tangent, east));

    // Curved polar plumes: a folded azimuth cosine slowly wanders with time.
    float wander = sin(azimuth * 3.0 + time * 0.03) * 0.55 +
                   sin(azimuth * 5.0 - time * 0.02) * 0.30;
    float plumes = 0.45 + 0.55 * pow(0.5 + 0.5 *
                   cos(azimuth * 11.0 + wander * 2.0), 2.0);
    float radial = smoothstep(0.55 * deg, 1.15 * deg, r) *
                   exp(-max(r - 1.0 * deg, 0.0) / (5.5 * deg)) *
                   (1.0 - smoothstep(12.0 * deg, 16.0 * deg, r));
    vec3 colour = vec3(0.82, 0.88, 1.0) * radial * plumes * 0.20;

    // The streamer belt is wider near the solar equator than over the poles.
    float equator = pow(0.5 + 0.5 * cos(azimuth * 2.0 + 0.6), 2.0);
    colour += vec3(0.72, 0.80, 1.0) * radial * equator * 0.10;

    // Chromospheric prominences: cool red tongues just above the limb.
    float limb = exp(-pow((r - 0.62 * deg) / (0.07 * deg), 2.0));
    float prominence = pow(max(cos(azimuth * 7.0 + 1.3), 0.0), 10.0);
    colour += vec3(1.0, 0.28, 0.16) * limb * prominence * 0.90;

    return colour * eclipse;
}
#endif
