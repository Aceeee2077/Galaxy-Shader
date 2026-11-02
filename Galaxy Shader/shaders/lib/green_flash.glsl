#ifndef SE_GREEN_FLASH
#define SE_GREEN_FLASH

// At the last moment of sunset the atmosphere refracts the solar limb into a
// brief green arc. The real event lasts about a second, so this is deliberately
// confined to the top edge of the disk and to a very narrow solar-elevation
// window. The disk frame uses the same angular radius as the visible sun.
// The mask is shared with the sky pass, which dims the warm disk underneath the
// green rim so the additive term is not washed out by the full solar radiance.
float greenFlashMask(vec3 ray, vec3 sun, float sunRadiusDegrees) {
    float gate = smoothstep(-0.030, -0.004, sun.y) *
                 (1.0 - smoothstep(0.012, 0.040, sun.y));
    if (gate <= 0.0 || ray.y < -0.01) return 0.0;

    vec3 helper = abs(sun.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(sun, helper));
    vec3 up = cross(right, sun);
    float sinR = sin(radians(sunRadiusDegrees));
    float x = dot(ray, right) / max(sinR, 1e-5);
    float y = dot(ray, up) / max(sinR, 1e-5);
    float r2 = x * x + y * y;

    // A thin ring just outside the limb, and only on its upper half.
    float rim = exp(-pow((r2 - 1.0) / 0.16, 2.0));
    float top = smoothstep(0.35, 0.85, y);
    return rim * top * gate;
}

vec3 greenFlash(vec3 ray, vec3 sun, float visibility, float sunRadiusDegrees) {
    if (visibility <= 0.0) return vec3(0.0);
    float flash = greenFlashMask(ray, sun, sunRadiusDegrees);
    if (flash <= 0.0) return vec3(0.0);

    vec3 helper = abs(sun.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(sun, helper));
    vec3 up = cross(right, sun);
    float y = dot(ray, up) / max(sin(radians(sunRadiusDegrees)), 1e-5);
    vec3 tint = mix(vec3(0.10, 0.88, 0.30), vec3(0.28, 0.92, 0.78),
                    smoothstep(0.75, 1.25, y));
    return tint * flash * visibility * 0.60;
}
#endif
