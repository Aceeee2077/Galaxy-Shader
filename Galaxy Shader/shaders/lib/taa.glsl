#ifndef SE_TAA
#define SE_TAA

vec3 rgbToYCoCg(vec3 c) {
    return vec3(c.r * 0.25 + c.g * 0.5 + c.b * 0.25,
                c.r * 0.5 - c.b * 0.5,
               -c.r * 0.25 + c.g * 0.5 - c.b * 0.25);
}

vec3 yCoCgToRgb(vec3 c) {
    return vec3(c.x + c.y - c.z, c.x + c.z, c.x - c.y - c.z);
}

// Reconstruct the current fragment in camera-relative player space and move it
// into the previous camera before projection. Sky directions deliberately omit
// translation: a camera turn should reproject the sky, a camera step should not.
bool temporalReprojection(vec2 uv, float depth, out vec2 previousUV,
                          out float expectedPreviousDepth) {
    vec3 view = viewPosition(uv, depth);
    vec4 previousClip;
    if (skyDepth(depth) > 0.5) {
        vec3 worldRay = worldDirection(view);
        vec3 previousView = mat3(gbufferPreviousModelView) * worldRay;
        previousClip = gbufferPreviousProjection * vec4(previousView, 0.0);
        expectedPreviousDepth = 1.0;
    } else {
        vec3 player = playerPosition(view);
        vec3 previousPlayer = player + cameraPosition - previousCameraPosition;
        vec3 previousView = (gbufferPreviousModelView * vec4(previousPlayer, 1.0)).xyz;
        previousClip = gbufferPreviousProjection * vec4(previousView, 1.0);
        expectedPreviousDepth = clamp(-previousView.z / max(far, 1.0), 0.0, 0.999);
    }
    if (previousClip.w <= 1e-6) return false;
    previousUV = previousClip.xy / previousClip.w * 0.5 + 0.5;
    return screenInside(previousUV) > 0.5;
}

float temporalDepth(vec2 uv, float depth) {
    if (skyDepth(depth) > 0.5) return 1.0;
    return clamp(-viewPosition(uv, depth).z / max(far, 1.0), 0.0, 0.999);
}

// A 3x3 YCoCg box is deliberately conservative. It removes chromatic and
// emissive trails while retaining more luminance detail than an RGB clamp.
vec3 clampTemporalHistory(sampler2D current, vec2 uv, vec3 history) {
    vec3 lo = vec3(1e20), hi = vec3(-1e20);
    vec2 px = pixelSize();
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            vec2 suv = clamp(uv + vec2(x, y) * px, px * 0.5, 1.0 - px * 0.5);
            vec3 sampleColor = rgbToYCoCg(texture2D(current, suv).rgb);
            lo = min(lo, sampleColor);
            hi = max(hi, sampleColor);
        }
    }
    return max(yCoCgToRgb(clamp(rgbToYCoCg(history), lo, hi)), vec3(0.0));
}

vec4 resolveTemporal(vec2 uv) {
    vec3 current = texture2D(colortex0, uv).rgb;
    float depth = texture2D(depthtex0, uv).r;
    float storedDepth = temporalDepth(uv, depth);
#if TAA_QUALITY == 0
    return vec4(current, storedDepth);
#else
    // Hands and large camera discontinuities have no reliable per-object motion.
    if (texture2D(colortex3, uv).b > 0.5 ||
        distance(cameraPosition, previousCameraPosition) > 8.0) {
        return vec4(current, storedDepth);
    }

    vec2 previousUV;
    float expectedDepth;
    if (!temporalReprojection(uv, depth, previousUV, expectedDepth)) {
        return vec4(current, storedDepth);
    }

    vec4 historySample = texture2D(colortex7, previousUV);
    float depthTolerance = max(0.0015, expectedDepth * 0.018);
    if (historySample.a <= 0.0 || abs(historySample.a - expectedDepth) > depthTolerance) {
        return vec4(current, storedDepth);
    }

    vec3 history = clampTemporalHistory(colortex0, uv, historySample.rgb);
#if TAA_QUALITY == 1
    float baseWeight = 0.82;
#elif TAA_QUALITY == 2
    float baseWeight = 0.88;
#else
    float baseWeight = 0.92;
#endif
    float motionPixels = length((previousUV - uv) * vec2(viewWidth, viewHeight));
    float motionWeight = 1.0 - smoothstep(0.5, 18.0, motionPixels);
    float colorDelta = abs(luminance(history) - luminance(current)) /
                       max(max(luminance(history), luminance(current)), 0.08);
    float reactiveWeight = 1.0 - smoothstep(0.08, 0.65, colorDelta);
    float historyWeight = baseWeight * mix(0.35, 1.0, motionWeight) *
                          mix(0.25, 1.0, reactiveWeight);
    return vec4(mix(current, history, historyWeight), storedDepth);
#endif
}

#endif
