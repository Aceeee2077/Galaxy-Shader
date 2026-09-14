#ifndef SE_LIGHTING
#define SE_LIGHTING
#include "/lib/pbr.glsl"
#include "/lib/clouds.glsl"
#include "/lib/shadows.glsl"
vec3 ambientRadiance(vec3 n, float sky) {
#if DIMENSION == -1
    return mix(vec3(0.075,0.025,0.009),toLinear(fogColor)*0.35,0.45)*(0.75+0.25*max(n.y,0.0));
#elif DIMENSION == 1
    return vec3(0.055,0.049,0.073)*(0.8+0.2*max(n.y,0.0));
#else
    float hemi=0.50+0.50*max(n.y,0.0);
    vec3 outdoor=mix(vec3(0.018,0.022,0.031)*NIGHT_BRIGHTNESS,vec3(0.27,0.32,0.38),dayAmount());
    outdoor=mix(outdoor,vec3(luminance(outdoor))*vec3(0.84,0.90,1.0),weatherOvercastAmount()*0.46);
    outdoor*=1.0-0.42*weatherStormAmount();
    return vec3(0.007)+outdoor*pow(sky,2.0)*hemi;
#endif
}
vec3 shadeSurface(Material m, vec3 player, vec2 lm, float id) {
    vec3 v=safeNormalize(-player);
    vec3 light=lightDirection();
    float nl=max(dot(m.normal,light),0.0);
    float shadow=1.0;
    vec3 direct=vec3(0.0);
#if DIMENSION == 0
    if (nl>0.0 && lm.y>0.02) shadow=shadowVisibility(player,m.normal,true);
    shadow*=vCloudShadow*smoothstep(0.02,0.40,lm.y);
    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*directionalRadiance()*shadow;
#endif
    float block=pow(lm.x,3.0)*1.4;
    vec3 ambient=ambientRadiance(m.normal,lm.y)*m.ao;
    vec3 blockColor=vec3(1.0,0.63,0.32);
    // Vanilla lightmap stores brightness only; mapped sources provide their own emission.
    vec3 result=direct+m.albedo*(ambient+blockColor*block);
    float held=float(max(heldBlockLightValue,heldBlockLightValue2))/15.0;
    int heldId=heldBlockLightValue>=heldBlockLightValue2 ? heldItemId : heldItemId2;
    float handLight=held*held*max(0.0,1.0-length(player)/12.0);
    result+=m.albedo*emissionTint(float(heldId))*handLight*handLight*0.7;
    result+=m.albedo*m.emission*5.0;
    result+=m.albedo*lightningBoltPosition.w*lm.y*vec3(1.1,1.2,1.4);
    result=mix(result,max(result,m.albedo*0.65),nightVision);
    return max(result,vec3(0.0));
}
#endif
