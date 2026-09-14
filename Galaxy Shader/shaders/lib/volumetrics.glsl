#ifndef SE_VOLUMETRICS
#define SE_VOLUMETRICS
#include "/lib/shadows.glsl"
#include "/lib/weather.glsl"
vec3 volumetricLight(vec3 player) {
    vec3 result=vec3(0.0);
#if VOLUMETRIC_QUALITY > 0 && DIMENSION == 0
    if(isEyeInWater!=0) return result;
    float lengthRay=min(length(player),min(shadowDistance,96.0));
    vec3 ray=safeNormalize(player);
    float forward=max(dot(ray,lightDirection()),0.0);
    float broadPhase=pow(forward,5.0)*0.72+pow(forward,18.0)*1.35+0.035;
    float lowSun=dawnDuskAmount();
    float canopy=1.0-smoothstep(0.54,0.96,float(eyeBrightnessSmooth.y)/240.0);
    int count=VOLUMETRIC_QUALITY*6;
    float rain=weatherRainAmount(), storm=weatherStormAmount();
    float density=(0.00065+lowSun*0.00125+rain*0.0028+storm*0.0015)*FOG_DENSITY;
    float cloudFactor=cloudShadow(ray*(lengthRay*0.5)+cameraPosition);
    float visibility=0.0, visibilitySquared=0.0;
    float jitter=hash12(gl_FragCoord.xy);
#if TAA_QUALITY > 0
    // An eight-frame phase is safe because the resolved image is accumulated.
    jitter=fract(jitter+float(frameCounter%8)*0.61803398875);
#endif
    for(int i=0;i<24;++i) {
        if(i>=count) break;
        float t=(float(i)+jitter)/float(count)*lengthRay;
        vec3 p=ray*t;
        float lit=shadowVisibility(p,vec3(0.0),false)*cloudFactor;
        float transmittance=exp(-t*density);
        visibility+=lit*transmittance;
        visibilitySquared+=lit*lit*transmittance;
    }
    float mean=visibility/float(count);
    float variance=max(visibilitySquared/float(count)-mean*mean,0.0);
    // Alternating lit/shadowed samples indicate foliage or terrain gaps and form
    // visible shafts. Low sun and forest shade strengthen them; noon suppresses.
    float shaftContrast=sqrt(variance)*(0.55+canopy*1.1)*lowSun;
    float extinction=1.0-exp(-lengthRay*density);
    result=directionalRadiance()*(mean*broadPhase+shaftContrast*1.7)*
           extinction*GODRAY_STRENGTH;
    result+=lightningBoltPosition.w*vec3(0.22,0.30,0.48)*
            extinction*(rain*0.45+storm*0.85);
    result=min(result,vec3(1.15));
#endif
    return result;
}
#endif
