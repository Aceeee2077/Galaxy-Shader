#ifndef SE_COMET_ANTITAIL
#define SE_COMET_ANTITAIL

// Seen from near a comet's orbital plane, the larger dust grains spread into a
// thin sunward spike called the anti-tail. It points opposite the ordinary dust
// tail, is much narrower than the tail and fades quickly away from the head.
vec3 cometAntitail(vec3 ray, float amount) {
    if (amount <= 0.0) return vec3(0.0);
    vec3 head = normalize(vec3(-0.35, 0.30, -0.88));
    vec3 tailDir = normalize(vec3(0.30, -0.55, 0.35));
    vec3 alongDir = -tailDir - head * dot(-tailDir, head);
    float alongLength = length(alongDir);
    if (alongLength < 1e-4) return vec3(0.0);
    alongDir /= alongLength;
    vec3 crossDir = cross(head, alongDir);

    float cosHead = clamp(dot(ray, head), -1.0, 1.0);
    float along = acos(cosHead);
    if (along > 0.22) return vec3(0.0); // about 12.6 degrees
    vec3 tangent = normalize(ray - head * cosHead);
    if (dot(tangent, alongDir) <= 0.0) return vec3(0.0);
    float across = asin(clamp(dot(tangent, crossDir), -1.0, 1.0));
    float width = 0.006 + 0.020 * along;
    float spike = exp(-pow(across / width, 2.0)) *
                  smoothstep(0.0, 0.010, along) *
                  exp(-along / 0.085) *
                  (1.0 - smoothstep(0.16, 0.22, along));
    float dust = 0.55 + 0.45 * 0.5 *
                 (valueNoise(ray.xz * 30.0) + valueNoise(ray.yz * 30.0 + 7.3));
    return vec3(0.72, 0.82, 1.0) * spike * dust * amount * 0.22;
}
#endif
