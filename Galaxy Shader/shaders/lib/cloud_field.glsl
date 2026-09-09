#ifndef SE_CLOUD_FIELD
#define SE_CLOUD_FIELD
// Compile-time field shared by geometry vertex evaluation and fragment functions.
// Include after /lib/common.glsl: cloudShadow() needs lightDirection().
#include "/lib/noise.glsl"

float cloudDensity(vec2 position) {
    vec2 p = position*0.0025+vec2(frameTimeCounter*0.009*CLOUD_SPEED,0.0);
    float n = fbm(p, min(CLOUD_QUALITY+2,6));
    float cover = CLOUD_COVERAGE + rainStrength*0.19 + thunderStrength*0.07;
    return smoothstep(0.72-cover*0.50,0.90-cover*0.50,n);
}

float cloudShadow(vec3 world) {
#if DIMENSION == 0 && CLOUD_QUALITY > 0
    vec3 l = lightDirection();
    vec2 p = world.xz+l.xz*clamp((280.0-world.y)/max(l.y,0.08),0.0,4000.0);
    return 1.0-cloudDensity(p)*(0.32+rainStrength*0.28);
#else
    return 1.0;
#endif
}
#endif
