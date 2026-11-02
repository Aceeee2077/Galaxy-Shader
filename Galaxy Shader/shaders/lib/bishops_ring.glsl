#ifndef SE_BISHOPS_RING
#define SE_BISHOPS_RING

// Bishop's ring: a broad, faint aureole around the sun produced by fine
// stratospheric dust. It has a warm brown-pink inner edge and a pale
// blue-white outer skirt, much wider and softer than an ice-crystal halo.
// The whole feature is analytic and adds no texture or render target.
vec3 bishopsRing(vec3 ray, vec3 sun, float day, float overcast) {
    if (day <= 0.0 || overcast >= 0.98 || sun.y <= 0.03) return vec3(0.0);
    float cosAngle = dot(ray, sun);
    if (cosAngle < 0.65) return vec3(0.0); // about 49 degrees

    const float deg = PI / 180.0;
    float angle = acos(clamp(cosAngle, -1.0, 1.0));
    float inner = smoothstep(13.0 * deg, 20.0 * deg, angle);
    float outer = 1.0 - smoothstep(38.0 * deg, 47.0 * deg, angle);
    float ring = exp(-pow((angle - 24.0 * deg) / (6.5 * deg), 2.0)) *
                 inner * outer;
    if (ring <= 0.0) return vec3(0.0);

    // Brown-pink dust at the inner edge fades to a cool pale-blue skirt.
    vec3 tint = mix(vec3(0.62, 0.38, 0.30), vec3(0.66, 0.78, 0.94),
                    smoothstep(18.0 * deg, 33.0 * deg, angle));
    return tint * ring * day * (1.0 - sat(overcast)) * 0.014;
}
#endif
