#ifndef SE_ANTISOLAR_RAYS
#define SE_ANTISOLAR_RAYS
#include "/lib/noise.glsl"

// Anticrepuscular rays converge on the anti-solar point. Cloud shadows make the
// alternating bright and dark spokes; here they are an analytic fan in the
// anti-solar frame. The fan only appears while the sun is near the horizon and
// only in the half of the sky opposite the sun, so no other direction pays for
// the trigonometry.
vec3 anticrepuscularRays(vec3 ray, vec3 sun, float overcast) {
    float lowSun = smoothstep(-0.10, -0.01, sun.y) *
                   (1.0 - smoothstep(0.14, 0.26, sun.y));
    float clear = 1.0 - 0.65 * sat(overcast);
    if (lowSun * clear <= 0.0 || ray.y <= 0.0) return vec3(0.0);

    vec3 anti = -sun;
    if (dot(ray, anti) <= 0.0) return vec3(0.0);

    vec3 right = normalize(cross(anti, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, anti);
    float azimuth = atan(dot(ray, up), dot(ray, right));
    float distance = acos(clamp(dot(ray, anti), -1.0, 1.0));

    // Spokes converge at the anti-solar point, so brightness depends on the
    // angle around it rather than on radius. Two incommensurate harmonics keep
    // the fan from looking like a regular optical grating.
    float wobble = 0.9 * sin(azimuth * 3.0 + frameTimeCounter * 0.006) +
                   0.5 * sin(azimuth * 9.0 - frameTimeCounter * 0.003);
    float streak = 0.5 + 0.5 * sin(azimuth * 8.0 + wobble);
    streak = pow(streak, 2.6);

    float radial = smoothstep(0.04, 0.18, distance) *
                   (1.0 - smoothstep(1.05, 1.32, distance));
    float dust = 0.75 + 0.25 * valueNoise(vec2(azimuth * 5.0,
                                               distance * 3.0) +
                                         frameTimeCounter * 0.002);

    vec3 tint = mix(vec3(0.72, 0.58, 0.54), vec3(1.0, 0.74, 0.54),
                    smoothstep(0.0, 0.16, sun.y + 0.02));
    return tint * streak * radial * dust * lowSun * clear * 0.035;
}
#endif
