#ifndef SE_AURORA_CORONA
#define SE_AURORA_CORONA

// Looking up along the magnetic field line turns an auroral curtain into a
// corona: bright rays converging on the zenith. The real display depends on the
// observer's magnetic latitude; here the existing aurora strength stands in for
// it, and the rays are a folded azimuth pattern inside a soft zenith cap.
vec3 auroraCorona(vec3 ray, float strength, float time) {
    if (strength <= 0.0 || ray.y <= 0.55) return vec3(0.0);
    float zenith = acos(clamp(ray.y, -1.0, 1.0));
    float azimuth = atan(ray.z, ray.x);
    float wobble = sin(azimuth * 4.0 + time * 0.05) * 0.05 +
                   sin(azimuth * 9.0 - time * 0.03) * 0.02;
    float rays = pow(0.5 + 0.5 * cos(azimuth * 14.0 + wobble * 9.0 +
                                     time * 0.02), 3.0);
    float cap = exp(-pow(zenith / 0.46, 2.0));
    float flicker = 0.72 + 0.28 * sin(time * 0.12 + azimuth * 3.0);
    vec3 tint = mix(vec3(0.10, 0.55, 0.30), vec3(0.34, 0.12, 0.46),
                    smoothstep(0.20, 0.80, zenith));
    return tint * rays * cap * flicker * strength * 0.085;
}
#endif
