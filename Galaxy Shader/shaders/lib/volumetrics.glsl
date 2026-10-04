#ifndef SE_VOLUMETRICS
#define SE_VOLUMETRICS
#include "/lib/shadows.glsl"
#include "/lib/weather.glsl"
vec3 volumetricLight(vec3 player, bool sky) {
    vec3 result=vec3(0.0);
#if VOLUMETRIC_QUALITY > 0 && DIMENSION == 0
    if(isEyeInWater==1) {
        // Underwater shafts: shorter integration, blue-green scattering and a
        // stronger forward lobe so the surface sun reads through the volume.
        float lengthRay=min(length(player),72.0);
        vec3 ray=safeNormalize(player);
        float forward=max(dot(ray,lightDirection()),0.0);
        int count=VOLUMETRIC_QUALITY*3;
        float density=0.0035*FOG_DENSITY;
        float visibility=0.0;
        float jitter=hash12(gl_FragCoord.xy);
#if TAA_QUALITY > 0
        jitter=fract(jitter+float(frameCounter%8)*0.61803398875);
#endif
        for(int i=0;i<20;++i) {
            if(i>=count) break;
            float t=(float(i)+jitter)/float(count)*lengthRay;
            vec3 p=ray*t;
            float lit=shadowVisibility(p,vec3(0.0),false);
            visibility+=lit*exp(-t*density);
        }
        float mean=visibility/float(count);
        float extinction=1.0-exp(-lengthRay*density);
        vec3 waterLight=mix(vec3(0.05,0.28,0.32),vec3(0.10,0.45,0.50),dayAmount());
        result=waterLight*mean*(0.30+0.70*pow(forward,3.0))*extinction*GODRAY_STRENGTH*0.55;
        return min(result,vec3(0.35));
    }
    if(isEyeInWater!=0) return result;
    float lengthRay=min(length(player),shadowDistance);
    vec3 ray=safeNormalize(player);
    float forward=max(dot(ray,lightDirection()),0.0);
    // The isotropic floor stays small on purpose, and on sky pixels it is nearly
    // gone: the procedural sky already carries its own atmospheric path, so a
    // larger constant added sun-coloured scatter over the whole dome and turned
    // a clear low sun into flat overcast haze. The forward lobes keep the
    // sunward shafts fully intact.
    float isotropicFloor = sky ? 0.0012 : 0.010;
    float broadPhase=pow(forward,4.0)*0.85+pow(forward,16.0)*1.45+isotropicFloor;
    float lowSun=dawnDuskAmount();
    float morningHaze=lowSun*DAWN_HAZE;
    float canopy=1.0-smoothstep(0.54,0.96,float(eyeBrightnessSmooth.y)/240.0);
    int count=VOLUMETRIC_QUALITY*8;
    // Rays towards the zenith integrate a short, mostly empty path. The
    // reference pack drops its shaft budget from 20 horizon steps to 4 straight
    // up, so well above the horizon this halves the sample count.
    if(ray.y>0.30) count=max(count/2,4);
    float rain=weatherRainAmount(), storm=weatherStormAmount();
    float density=(0.00065+morningHaze*0.0011+rain*0.0034+storm*0.0015)*FOG_DENSITY;
    float cloudFactor=cloudShadow(ray*(lengthRay*0.5)+cameraPosition);
    float visibility=0.0, visibilitySquared=0.0;
    float jitter=hash12(gl_FragCoord.xy);
#if TAA_QUALITY > 0
    // An eight-frame phase is safe because the resolved image is accumulated.
    jitter=fract(jitter+float(frameCounter%8)*0.61803398875);
#endif
    for(int i=0;i<40;++i) {
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
    // A shaft seen from the side scatters far less light toward the eye than one
    // seen against the sun. Without this lobe the beam energy lit the entire
    // dome evenly, so a clear morning sky matched an overcast one.
    float shaftPhase=0.10+0.90*pow(forward,2.0);
    float extinction=1.0-exp(-lengthRay*density);
    result=directionalRadiance()*(mean*broadPhase+shaftContrast*1.7*shaftPhase)*
           extinction*GODRAY_STRENGTH;
    result+=lightningBoltPosition.w*vec3(0.22,0.30,0.48)*
            extinction*(rain*0.45+storm*0.85);
    result=min(result,vec3(1.15));
#endif
    return result;
}
#endif
