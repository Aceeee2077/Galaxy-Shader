#ifndef SE_GTAO
#define SE_GTAO

// A compact GTAO-style horizon search. Samples are grouped into screen-space
// directions, but their radius is projected from a 1.5-block world radius.
// Depth and normal weights act as a bilateral guard at silhouettes.
float gtaoVisibility(vec2 uv, vec3 view, vec3 worldNormal) {
#if AO_QUALITY == 0 || DIMENSION != 0
    return 1.0;
#else
    vec3 viewNormal = safeNormalize(mat3(gbufferModelView) * worldNormal);
    const float radius = 1.5;
    vec2 radiusUV = vec2(gbufferProjection[0][0], gbufferProjection[1][1]) *
                    radius / max(-view.z, 1.0) * 0.5;
    radiusUV = min(radiusUV, vec2(0.14));
#if AO_QUALITY == 1
    const int directions = 4;
    const int steps = 2;
#elif AO_QUALITY == 2
    const int directions = 6;
    const int steps = 3;
#else
    const int directions = 8;
    const int steps = 4;
#endif
    float occlusion = 0.0;
    float directionWeight = 0.0;
    float rotation = hash12(floor(gl_FragCoord.xy * 0.25)) * 2.0 * PI;
    for (int directionIndex = 0; directionIndex < directions; ++directionIndex) {
        float angle = (float(directionIndex) + 0.5) * 2.0 * PI /
                      float(directions) + rotation;
        vec2 direction = vec2(cos(angle), sin(angle));
        float horizon = 0.0;
        float valid = 0.0;
        for (int stepIndex = 1; stepIndex <= steps; ++stepIndex) {
            float fraction = float(stepIndex) / float(steps);
            vec2 suv = uv + direction * radiusUV * fraction;
            if (screenInside(suv) < 0.5) continue;
            float sampleDepth = texture2D(depthtex1, suv).r;
            if (skyDepth(sampleDepth) > 0.5) continue;
            vec4 sampleMeta = texture2D(colortex3, suv);
            if (sampleMeta.a < 0.5 || sampleMeta.b > 0.5) continue;
            vec3 delta = viewPosition(suv, sampleDepth) - view;
            float distanceToSample = length(delta);
            if (distanceToSample < 0.025 || distanceToSample > radius) continue;
            vec3 sampleNormal = safeNormalize(mat3(gbufferModelView) *
                                (texture2D(colortex1, suv).xyz * 2.0 - 1.0));
            float normalWeight = smoothstep(-0.25, 0.35, dot(viewNormal, sampleNormal));
            float rangeWeight = 1.0 - smoothstep(radius * 0.2, radius, distanceToSample);
            float elevation = max(dot(viewNormal, delta / distanceToSample) - 0.06, 0.0);
            horizon = max(horizon, elevation * rangeWeight * normalWeight);
            valid += normalWeight;
        }
        if (valid > 0.0) {
            occlusion += horizon;
            directionWeight += 1.0;
        }
    }
    occlusion /= max(directionWeight, 1.0);
    return 1.0 - min(occlusion * 1.35, 0.42);
#endif
}

#endif
