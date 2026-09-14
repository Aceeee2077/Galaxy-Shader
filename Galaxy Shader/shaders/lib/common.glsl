#ifndef SE_COMMON
#define SE_COMMON
#include "/lib/settings.glsl"
uniform mat4 gbufferModelView, gbufferModelViewInverse;
uniform mat4 gbufferProjection, gbufferProjectionInverse;
uniform mat4 gbufferPreviousModelView, gbufferPreviousProjection;
uniform mat4 shadowModelView, shadowModelViewInverse, shadowProjection;
uniform vec3 cameraPosition, previousCameraPosition;
uniform vec3 sunPosition, moonPosition, shadowLightPosition;
uniform vec3 fogColor, skyColor;
uniform vec4 lightningBoltPosition;
uniform ivec2 eyeBrightnessSmooth;
uniform float viewWidth, viewHeight, near, far, frameTimeCounter;
uniform float rainStrength, wetness, thunderStrength, nightVision, blindness, darknessFactor;
uniform float centerDepthSmooth;
uniform int isEyeInWater, moonPhase, frameCounter;
uniform int heldItemId, heldItemId2, heldBlockLightValue, heldBlockLightValue2;
const float PI = 3.14159265359;
float sat(float x) { return clamp(x, 0.0, 1.0); }
vec3 safeNormalize(vec3 v) { return v * inversesqrt(max(dot(v,v), 1e-12)); }
float luminance(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec2 pixelSize() { return 1.0 / max(vec2(viewWidth, viewHeight), vec2(1.0)); }
vec3 toLinear(vec3 c) { return pow(max(c, vec3(0.0)), vec3(2.2)); }
vec3 viewPosition(vec2 uv, float d) {
    vec4 p = gbufferProjectionInverse * vec4(uv * 2.0 - 1.0, d * 2.0 - 1.0, 1.0);
    return p.xyz / (abs(p.w) < 1e-7 ? 1e-7 : p.w);
}
vec3 playerPosition(vec3 view) { return (gbufferModelViewInverse * vec4(view,1.0)).xyz; }
vec3 worldDirection(vec3 view) { return safeNormalize(mat3(gbufferModelViewInverse) * view); }
vec3 sunDirection() { return worldDirection(sunPosition); }
vec3 lightDirection() { return worldDirection(shadowLightPosition); }
float dayAmount() { return smoothstep(-0.10, 0.12, sunDirection().y); }
float skyDepth(float d) { return step(0.999999, d); }
vec2 projectView(vec3 p) {
    vec4 h = gbufferProjection * vec4(p, 1.0);
    return h.xy / max(h.w, 1e-6) * 0.5 + 0.5;
}
float screenInside(vec2 uv) { return step(0.0,min(uv.x,uv.y)) * step(max(uv.x,uv.y),1.0); }
#endif
