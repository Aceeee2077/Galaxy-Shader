#ifndef SE_ZODIACAL_BAND
#define SE_ZODIACAL_BAND

// After astronomical twilight the zodiacal cloud is no longer a sunward cone:
// it reads as a faint band along the ecliptic, brightest around the anti-solar
// point (the gegenschein). The ecliptic is approximated by the plane containing
// the sun direction and the celestial pole (world Z, the vanilla rotation axis).
vec3 zodiacalBand(vec3 ray, vec3 sun, float overcast) {
    float night = smoothstep(0.12, 0.34, -sun.y);
    float clear = 1.0 - sat(overcast);
    if (night <= 0.0 || clear <= 0.0 || ray.y <= 0.0) return vec3(0.0);

    vec3 normal = normalize(cross(vec3(0.0, 0.0, 1.0), sun));
    float latitude = dot(ray, normal);
    float band = exp(-pow(latitude / 0.055, 2.0));

    // The gegenschein is an oval, not a point: wider along the ecliptic than
    // across it. Build a local tangent frame around the anti-solar direction.
    const float deg = PI / 180.0;
    vec3 anti = -sun;
    vec3 along = normalize(cross(normal, anti));
    vec3 across = normal;
    float x = asin(clamp(dot(ray, along), -1.0, 1.0));
    float y = asin(clamp(dot(ray, across), -1.0, 1.0));
    float gegen = exp(-pow(x / (7.0 * deg), 2.0) -
                      pow(y / (4.0 * deg), 2.0));
    // The spot is only visible once it is clear of the horizon haze.
    gegen *= smoothstep(0.02, 0.12, ray.y);

    vec3 bandColour = vec3(0.55, 0.60, 0.72);
    vec3 gegenColour = vec3(0.74, 0.70, 0.60);
    return (bandColour * band * 0.015 + gegenColour * gegen * 0.030) *
           night * clear;
}
#endif
