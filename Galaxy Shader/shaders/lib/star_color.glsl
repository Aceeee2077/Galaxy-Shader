#ifndef SE_STAR_COLOR
#define SE_STAR_COLOR

// Stars differ in surface temperature and apparent brightness. Two stable
// hashes per star cell give a cool blue-white to warm orange tint and a
// magnitude scale, so the field stops looking like one white colour.
vec3 starColour(float magnitudeHash, float temperatureHash) {
    vec3 tint = mix(vec3(1.00, 0.70, 0.50), vec3(0.66, 0.78, 1.00),
                    clamp(temperatureHash, 0.0, 1.0));
    return tint * mix(0.65, 1.25, clamp(magnitudeHash, 0.0, 1.0));
}
#endif
