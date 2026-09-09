#ifndef SE_VOLUMETRICS
#define SE_VOLUMETRICS
#include "/lib/shadows.glsl"
vec3 volumetricLight(vec3 player) {
    vec3 result=vec3(0.0);
#if VOLUMETRIC_QUALITY > 0 && DIMENSION == 0
    if(isEyeInWater!=0) return result;
    float lengthRay=min(length(player),min(shadowDistance,96.0));
    vec3 ray=safeNormalize(player);
    float phase=pow(max(dot(ray,lightDirection()),0.0),8.0)*0.8+0.08;
    int count=VOLUMETRIC_QUALITY*6;
    float density=(0.0009+0.003*rainStrength)*FOG_DENSITY;
    float cloudFactor=cloudShadow(ray*(lengthRay*0.5)+cameraPosition);
    float visibility=0.0;
    for(int i=0;i<24;++i) {
        if(i>=count) break;
        float t=(float(i)+0.5)/float(count)*lengthRay;
        vec3 p=ray*t;
        visibility+=shadowVisibility(p,vec3(0.0),false)*exp(-t*density)*cloudFactor;
    }
    result=directionalRadiance()*visibility/float(count)*phase*(1.0-exp(-lengthRay*density));
#endif
    return result;
}
#endif
