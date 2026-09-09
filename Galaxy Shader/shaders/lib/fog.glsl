#ifndef SE_FOG
#define SE_FOG
#include "/lib/atmosphere.glsl"
vec3 applyFog(vec3 color, vec3 player, bool sky) {
    float distanceToEye=length(player);
    vec3 ray=safeNormalize(player);
    float density=0.0;
    vec3 scatter=vec3(0.0);
    if(isEyeInWater==1) {
        vec3 absorb=exp(-vec3(0.20,0.075,0.040)*distanceToEye*FOG_DENSITY);
        float eyeSky=float(eyeBrightnessSmooth.y)/240.0;
        vec3 under=vec3(0.012,0.085,0.105)*mix(0.2,1.0,eyeSky*dayAmount());
        color=color*absorb+under*(1.0-absorb);
    } else if(isEyeInWater==2) {
        color=mix(color,vec3(1.1,0.17,0.005),1.0-exp(-distanceToEye*1.6));
    } else if(isEyeInWater==3) {
        color=mix(color,vec3(0.65,0.77,0.88),1.0-exp(-distanceToEye*0.6));
    } else {
#if DIMENSION == -1
        density=0.016;
        scatter=mix(toLinear(fogColor),vec3(0.20,0.045,0.012),0.35);
#elif DIMENSION == 1
        density=0.0035;
        scatter=vec3(0.018,0.012,0.027);
#else
        float outdoor=smoothstep(0.04,0.6,float(eyeBrightnessSmooth.y)/240.0);
        float worldHeight=cameraPosition.y+player.y*0.5;
        float heightFog=exp(-max(worldHeight-63.0,0.0)/65.0);
        float morning=(1.0-smoothstep(0.05,0.3,abs(sunDirection().y)))*0.001;
        density=mix(0.0012,(0.0012+morning+rainStrength*0.006+thunderStrength*0.006)*heightFog,outdoor);
        scatter=mix(vec3(0.008,0.009,0.012),atmosphere(ray,false),outdoor);
#endif
        float amount=1.0-exp(-distanceToEye*density*FOG_DENSITY);
        if(!sky) amount=max(amount,smoothstep(far*0.72,far*0.99,length(player.xz)));
        color=mix(color,scatter,sat(amount));
    }
    float impaired=max(blindness,darknessFactor*0.85);
    color*=exp(-distanceToEye*impaired*0.18)*(1.0-impaired*0.65);
    return color;
}
#endif
