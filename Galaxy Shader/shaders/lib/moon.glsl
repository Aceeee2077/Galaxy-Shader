#ifndef SE_MOON
#define SE_MOON
#include "/lib/noise.glsl"

// Just smaller than the 2 degree solar radius: the pair reads as a matched
// sun/moon while the disk still fits comfortably inside the halo.
const float MOON_ANGULAR_RADIUS = 1.9; // degrees

// Minecraft cycles moonPhase 0..7: 0 is full, 4 is new, 2 and 6 are quarters.
float moonPhaseFraction() {
    return 0.5 + 0.5 * cos(PI * float(moonPhase) / 4.0);
}

// Analytic moon: phase terminator, procedural maria/craters, earthshine and a
// compact halo. The halo is evaluated only within ~25 degrees of the moon; all
// other sky pixels leave after one dot product. Returns HDR radiance.
vec3 moonSky(vec3 ray, float night, float overcast) {
    if (night <= 0.0) return vec3(0.0);
    vec3 dir = safeNormalize(worldDirection(moonPosition));
    float mu = dot(ray, dir);
    if (mu < 0.90) return vec3(0.0);

    float radius = radians(MOON_ANGULAR_RADIUS);
    float cosR = cos(radius);
    float sinR = sin(radius);
    float angular = acos(clamp(mu, -1.0, 1.0));
    float litFraction = moonPhaseFraction();

    // A world-up basis keeps the maria upright while the moon crosses the sky.
    // The zenith case needs a different helper to avoid a degenerate cross.
    vec3 helper = abs(dir.y) > 0.98 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(dir, helper));
    vec3 up = cross(right, dir);

    float visibility = night * (1.0 - 0.94 * overcast);

    vec3 result = vec3(0.0);
    if (mu >= cosR) {
        float x = dot(ray, right) / max(sinR, 1e-4);
        float y = dot(ray, up) / max(sinR, 1e-4);
        float r2 = x * x + y * y;
        float edge = max(fwidth(r2) * 1.5, 1e-4);
        float disk = 1.0 - smoothstep(1.0 - edge, 1.0 + edge * 0.5, r2);
        float limb = sqrt(max(1.0 - r2, 0.0));

        // Light reaches the disk from the sun's side. With moonPhase deciding
        // how much is illuminated, the terminator is the projected sphere
        // boundary at x = 1 - 2f.
        vec3 sun = worldDirection(sunPosition);
        float sunSide = dot(sun, right);
        // Point the bright limb at the sun when it has a horizontal component;
        // otherwise fall back to waxing/waning so phases 2 and 6 mirror.
        float side = sunSide > 0.05 ? 1.0 :
                     (sunSide < -0.05 ? -1.0 : (float(moonPhase) >= 5.0 ? 1.0 : -1.0));
        float aa = max(fwidth(x) * 1.5, 0.012);
        float terminator = x * side - (1.0 - 2.0 * litFraction);
        float lit = smoothstep(-aa, aa, terminator);

        // Two scales: broad dark maria and a finer crater speckle. Both stay
        // inside the disk, so the halo never pays for texture noise.
        float maria = valueNoise(vec2(x, y) * 2.7 + vec2(4.3, 1.7));
        float crater = valueNoise(vec2(x, y) * 11.0 + vec2(19.1, 7.4));
        float albedo = 0.87 - 0.19 * smoothstep(0.40, 0.76, maria)
                            - 0.07 * smoothstep(0.58, 0.86, crater);
        // The real Moon is retroreflective: only a gentle limb falloff.
        albedo *= 0.70 + 0.30 * limb;

        vec3 diskColor = vec3(0.96, 0.97, 1.0) * albedo * 1.55 * lit;
        // Earthshine: a faint cool fill on the unlit side, never a second moon.
        diskColor += vec3(0.010, 0.014, 0.022) * (1.0 - lit) * (0.4 + 0.6 * limb);
        result += diskColor * disk;
    }

    // Halo starts outside the limb so a new moon stays dark instead of being
    // padded by the inner glow. The wide term is the moonlit sky gradient.
    float outside = smoothstep(radius * 0.85, radius * 1.15, angular);
    float extra = max(angular - radius, 0.0);
    float halo = (exp(-extra * 45.0) * 0.075 + exp(-extra * 12.0) * 0.010) * outside;
    halo *= 0.05 + 0.95 * litFraction;
    result += vec3(0.72, 0.80, 1.0) * halo;
    result += vec3(0.38, 0.46, 0.62) * exp(-angular * 7.0) * 0.0035;

    return result * visibility;
}
#endif
