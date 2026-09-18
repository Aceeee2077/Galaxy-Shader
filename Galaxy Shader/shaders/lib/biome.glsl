#ifndef SE_BIOME
#define SE_BIOME

// Biome-aware atmosphere layer. Iris exposes temperature and rainfall for the
// biome under the camera, which is enough to build smooth regional moods
// without relying on hard-coded biome category IDs.
float biomeBlend() {
    return float(BIOME_BLEND);
}

float biomeHeat() {
    return sat((temperature + 0.4) / 2.4);
}

float biomeCold() {
    return 1.0 - smoothstep(-0.25, 0.45, temperature);
}

float biomeDesert() {
    return smoothstep(0.45, 0.85, temperature) * (1.0 - smoothstep(0.05, 0.30, rainfall));
}

float biomeJungle() {
    return smoothstep(0.55, 0.95, rainfall) * smoothstep(0.40, 0.85, temperature);
}

float biomeSwamp() {
    float wet = smoothstep(0.45, 0.85, rainfall);
    float mild = smoothstep(-0.15, 0.40, temperature);
    float notHot = 1.0 - smoothstep(0.35, 0.75, temperature);
    return wet * mild * notHot;
}

float biomeSavanna() {
    return smoothstep(0.30, 0.70, temperature) * (1.0 - smoothstep(0.20, 0.50, rainfall));
}

float biomeTaiga() {
    return smoothstep(-0.45, -0.05, temperature) * smoothstep(0.25, 0.65, rainfall);
}

// Regional fog colour and density multiplier. Dry regions thin the haze and
// warm it; humid and swamp regions thicken it with a cooler green cast.
vec3 biomeFogTint() {
    vec3 tint = vec3(1.0);
    tint = mix(tint, vec3(1.06, 0.92, 0.72), biomeDesert() * 0.35);
    tint = mix(tint, vec3(0.86, 1.04, 0.90), biomeJungle() * 0.35);
    tint = mix(tint, vec3(0.84, 1.00, 0.88), biomeSwamp() * 0.40);
    tint = mix(tint, vec3(1.04, 0.96, 0.86), biomeSavanna() * 0.30);
    tint = mix(tint, vec3(0.90, 0.97, 1.10), biomeCold() * 0.35);
    return mix(vec3(1.0), tint, biomeBlend());
}

float biomeFogDensity() {
    float delta = -0.25 * biomeDesert()
                +  0.35 * biomeJungle()
                +  0.50 * biomeSwamp()
                -  0.10 * biomeSavanna()
                +  0.06 * biomeTaiga();
    return 1.0 + delta * biomeBlend();
}

vec3 biomeAmbientTint() {
    vec3 tint = vec3(1.0);
    tint = mix(tint, vec3(1.05, 0.98, 0.88), biomeDesert() * 0.30);
    tint = mix(tint, vec3(0.90, 1.04, 0.92), biomeJungle() * 0.30);
    tint = mix(tint, vec3(0.88, 0.99, 0.92), biomeSwamp() * 0.30);
    tint = mix(tint, vec3(0.92, 0.98, 1.08), biomeCold() * 0.30);
    return mix(vec3(1.0), tint, biomeBlend());
}

vec3 biomeSkyTint() {
    vec3 tint = vec3(1.0);
    tint = mix(tint, vec3(1.05, 0.96, 0.84), biomeDesert() * 0.30);
    tint = mix(tint, vec3(0.94, 1.02, 1.00), biomeJungle() * 0.25);
    tint = mix(tint, vec3(0.92, 1.00, 1.02), biomeSwamp() * 0.25);
    tint = mix(tint, vec3(0.92, 0.98, 1.08), biomeCold() * 0.30);
    return mix(vec3(1.0), tint, biomeBlend());
}

float biomeAuroraBoost() {
    return mix(0.55, 1.70, biomeCold() * biomeBlend());
}

float biomeDustHaze() {
    return biomeDesert() * biomeBlend();
}

#endif
