#ifndef SE_FOG
#define SE_FOG
#include "/lib/atmosphere.glsl"
#include "/lib/weather.glsl"
#include "/lib/seasons.glsl"
#include "/lib/biome.glsl"
vec3 applyFog(vec3 color, vec3 player, bool sky) {
    float distanceToEye=length(player);
    vec3 ray=safeNormalize(player);
    float density=0.0;
    vec3 scatter=vec3(0.0);
    if(isEyeInWater==1) {
        vec3 absorb=exp(-WATER_ABSORPTION_UNDERWATER*distanceToEye*FOG_DENSITY);
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
        float targetHeight=cameraPosition.y+player.y;
        float midpointHeight=cameraPosition.y+player.y*0.5;
        float lowHeight=min(cameraPosition.y,targetHeight);
        float heightFog=exp(-max(midpointHeight-62.0,0.0)/42.0);
        float valleyHeight=exp(-max(lowHeight-66.0,0.0)/19.0);
        float morning=dawnDuskAmount();
        float overcast=weatherOvercastAmount();
        float rain=weatherRainAmount();
        float storm=weatherStormAmount();
        float valleyNoise=0.5;
#if TERRAIN_FOG_QUALITY > 0
        vec2 fogPosition=cameraPosition.xz+player.xz*0.55+
                         weatherWindDirection()*frameTimeCounter*1.4;
        valleyNoise=fbm(fogPosition*0.006,max(TERRAIN_FOG_QUALITY+1,2));
#endif
        float pockets=smoothstep(0.34,0.76,valleyNoise)*valleyHeight*
                      smoothstep(10.0,46.0,distanceToEye);
        float distanceHaze=0.00075+overcast*0.00075+rain*0.0010;
        float heightDensity=heightFog*(0.00045+morning*0.0038+rain*0.0024);
        float valleyDensity=pockets*(0.0010+morning*0.0060+rain*0.0038+storm*0.0024);
        density=mix(0.0010,distanceHaze+heightDensity+valleyDensity,outdoor);
        density*=mix(0.90,1.10,dayVariation())*biomeFogDensity();
        vec3 clearScatter=atmosphere(ray,false);
        vec3 wetScatter=mix(vec3(0.20,0.25,0.30),vec3(0.10,0.125,0.17),storm);
        float sunward=pow(max(dot(ray,sunDirection()),0.0),3.0);
        vec3 goldenHaze=sunlightColor()*vec3(0.66,0.60,0.49);
        clearScatter=mix(clearScatter,goldenHaze,morning*(0.38+sunward*0.45));
        wetScatter=mix(wetScatter,goldenHaze,morning*0.72);
        wetScatter*=mix(0.10,1.0,dayAmount());
        scatter=mix(vec3(0.008,0.009,0.012),mix(clearScatter,wetScatter,overcast*0.68),outdoor);
        scatter*=mix(0.94,1.06,dayVariation())*seasonFogTint()*biomeFogTint();
        scatter+=vec3(0.30,0.22,0.14)*biomeDustHaze()*outdoor*dayAmount()*0.25;
#if WEATHER_EFFECTS == 1
        float sandstorm=biomeDesert()*smoothstep(0.25,0.75,storm)*(1.0-rain*0.3);
        float blizzard=max(float(biome_precipitation==2),smoothstep(0.75,0.98,biomeCold()))*
                       smoothstep(0.10,0.50,rain+storm*0.4);
        float fogBank=smoothstep(0.45,0.85,valleyNoise)*smoothstep(0.20,0.70,overcast);
        density*=1.0+sandstorm*2.8+blizzard*1.6+fogBank*0.20;
        scatter=mix(scatter,vec3(0.48,0.34,0.19),sandstorm*0.55);
        scatter=mix(scatter,vec3(0.62,0.66,0.72),blizzard*0.40);
        scatter=mix(scatter,vec3(0.30,0.34,0.38),fogBank*0.12);
#endif
        scatter+=lightningBoltPosition.w*vec3(0.20,0.27,0.40)*
                 (rain*0.55+storm*0.45);
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
