#ifndef SE_SUPERNUMERARY
#define SE_SUPERNUMERARY

// Interference between the rays that form the primary bow leaves a few thin
// supernumerary arcs just inside the violet edge, where the bow is already
// fading. They alternate pale green and pink rather than showing a full
// spectrum. The term is a damped radial cosine over the 36-40 degree band and
// shares the rain or wetness gate of the primary.
vec3 supernumeraryArcs(vec3 ray, vec3 sun, float moisture, float overcast,
                       float day) {
    if (moisture <= 0.025 || sun.y <= 0.02 || ray.y <= 0.0) return vec3(0.0);
    float angle = acos(clamp(dot(ray, -sun), -1.0, 1.0));
    const float inner = 0.620; // about 35.5 degrees
    const float outer = 0.700; // just inside the violet edge
    if (angle <= inner || angle >= outer) return vec3(0.0);

    float across = (angle - inner) / (outer - inner);
    float envelope = smoothstep(0.0, 0.25, across) *
                     (1.0 - smoothstep(0.72, 1.0, across));
    float fringes = 0.5 + 0.5 * cos(across * 6.2831853 * 4.5);
    vec3 tint = mix(vec3(0.62, 0.78, 0.52), vec3(0.86, 0.62, 0.76), fringes);
    float clearSky = 1.0 - overcast * 0.72;
    return tint * fringes * envelope * smoothstep(0.0, 0.10, ray.y) *
           moisture * clearSky * day * 0.045;
}
#endif
