#ifndef SE_FOGBOW
#define SE_FOGBOW

// Fog droplets are much smaller than raindrops, so diffraction smears the
// refraction bow into a broad, nearly white arc at about 42 degrees from the
// anti-solar point. Only a faint warm outer rim and cool inner rim survive. The
// appearance needs fog with the sun behind the viewer and low enough that the
// bow clears the horizon. The term is an analytic radial band.
vec3 fogbow(vec3 ray, vec3 sun, float fogAmount, float day) {
    if (fogAmount <= 0.001 || day <= 0.0 || ray.y <= 0.0) return vec3(0.0);
    if (sun.y <= 0.01 || sun.y >= 0.67) return vec3(0.0);
    float angle = acos(clamp(dot(ray, -sun), -1.0, 1.0));
    const float inner = 0.698; // about 40 degrees
    const float span = 0.122;  // broad, out to about 47 degrees
    float radial = (angle - inner) / span;
    if (radial <= 0.0 || radial >= 1.0) return vec3(0.0);

    float band = smoothstep(0.0, 0.22, radial) *
                 (1.0 - smoothstep(0.72, 1.0, radial));
    vec3 tint = mix(vec3(0.70, 0.80, 1.0), vec3(1.0, 0.86, 0.70),
                    smoothstep(0.35, 0.95, radial));
    tint = mix(tint, vec3(1.0), 0.55);
    return tint * band * smoothstep(0.0, 0.08, ray.y) *
           fogAmount * day * 0.060;
}
#endif
