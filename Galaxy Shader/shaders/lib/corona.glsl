#ifndef SE_CORONA
#define SE_CORONA

// A lunar corona is diffraction by small cloud droplets, not refraction by ice
// crystals. It forms a compact set of pastel rings around the moon, blue-white
// nearest the disk and warmer at the outside, inside a few degrees. Here the
// rings are a radial cosine with a soft envelope, gated to night and scaled by
// the illuminated moon fraction. Rays beyond the envelope exit after one dot.
vec3 lunarCorona(vec3 ray, vec3 moonDir, float litFraction, float overcast,
                 float night) {
    if (night <= 0.0 || litFraction <= 0.05 || ray.y <= 0.0 ||
        moonDir.y <= 0.0) return vec3(0.0);
    float d = dot(ray, moonDir);
    if (d < 0.97) return vec3(0.0); // about 14 degrees

    float angle = acos(clamp(d, -1.0, 1.0));
    const float deg = PI / 180.0;
    float envelope = smoothstep(0.9 * deg, 2.2 * deg, angle) *
                     (1.0 - smoothstep(8.0 * deg, 13.0 * deg, angle));
    if (envelope <= 0.0) return vec3(0.0);

    float fringes = 0.5 + 0.5 * cos((angle - 1.1 * deg) *
                                    (6.2831853 / (2.0 * deg)));
    fringes *= fringes;
    vec3 tint = mix(vec3(0.62, 0.76, 1.0), vec3(1.0, 0.70, 0.56),
                    smoothstep(2.5 * deg, 7.5 * deg, angle));
    float weather = 1.0 - 0.75 * overcast;
    return tint * fringes * envelope * night * litFraction * weather * 0.10;
}
#endif
