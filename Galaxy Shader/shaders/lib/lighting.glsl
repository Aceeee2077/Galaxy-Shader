#ifndef SE_LIGHTING
#define SE_LIGHTING
#include "/lib/pbr.glsl"
#include "/lib/clouds.glsl"
#include "/lib/shadows.glsl"
#include "/lib/seasons.glsl"
#include "/lib/biome.glsl"
vec3 ambientRadiance(vec3 n, float sky) {
#if DIMENSION == -1
    return mix(vec3(0.075,0.025,0.009),toLinear(fogColor)*0.35,0.45)*(0.75+0.25*max(n.y,0.0));
#elif DIMENSION == 1
    // Cool violet ambient matching the rift core that lights the End.
    return vec3(0.135,0.135,0.170)*(0.65+0.35*max(n.y,0.0));
#else
    vec3 outdoor=skyIrradiance(n);
    float cave=1.0-smoothstep(0.02,0.28,sky);
    vec3 biolum=vec3(0.0015,0.0045,0.0042)*cave;
    return vec3(0.004)+outdoor*pow(sat(sky),2.0)*seasonAmbientTint()*biomeAmbientTint()+biolum;
#endif
}
vec3 shadeSurface(Material m, vec3 player, vec2 lm, float id) {
    vec3 v=safeNormalize(-player);
    vec3 light=lightDirection();
    float nl=max(dot(m.normal,light),0.0);
    float shadow=1.0;
    vec3 direct=vec3(0.0);
#if DIMENSION == 0
    float foliage=step(10000.5,id)*step(id,10005.5);
    if ((nl>0.0 || foliage>0.5) && lm.y>0.02) shadow=shadowVisibility(player,m.normal,true);
    shadow*=vCloudShadow*smoothstep(0.02,0.40,lm.y);
    // The direct, leaf-transmission and bounce lobes all share the same sun and
    // moon radiance. Evaluate it once: every call repeats the atmospheric
    // transmittance exponentials, and opaque terrain is the budget that decides
    // whether a low-end GPU keeps its frame rate.
    vec3 sunRadiance=directionalRadiance();
    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*sunRadiance*shadow;
    // Thin leaves/grass transmit a bounded warm lobe when viewed against the
    // sun. The same shadow visibility prevents transmission through terrain.
    float forward=pow(max(dot(-v,light),0.0),5.0);
    direct+=sqrt(max(m.albedo,vec3(0.0)))*foliage*(1.0-m.metal)*
            (0.06+0.36*forward)*(1.0-nl)*sunRadiance*shadow;
    // Warm bounce complements the sky probe in outdoor shade.
    // Lightmap and AO gates reject closed caves and deep crevices.
    direct+=m.albedo*(1.0-m.metal)*sunRadiance*0.035*
            (1.0-shadow)*pow(sat(lm.y),4.0)*m.ao;
    // Heiligenschein: on a dewy morning, droplets on grass and leaves focus
    // light straight back along the incoming ray, so the ground glows around
    // the antisolar point, where the observer's own shadow falls. The dew
    // window is the first hours after sunrise; rain replaces dew and dims it.
    if (foliage > 0.5) {
        float clock = float(worldTime % 24000);
        float dew = 1.0 - smoothstep(2000.0, 4600.0, clock);
        // A narrow backscatter lobe, about ten degrees wide at half height.
        // Six squarings keep it to multiplies on the low-end paths.
        float s = sat(dot(v, light));
        float s2 = s * s;
        float s4 = s2 * s2;
        float s8 = s4 * s4;
        float s16 = s8 * s8;
        float retro = s16 * s16 * s16; // s^48
        direct += m.albedo * sunRadiance * retro * dew * shadow *
                  (0.35 + 0.65 * nl) * 0.45 *
                  (1.0 - 0.70 * weatherRainAmount());
    }
#elif DIMENSION == 1
    shadow=shadowVisibility(player,m.normal,true);
    direct=(m.albedo*(1.0-m.metal)*nl+specularBRDF(m,v,light))*vec3(0.90,0.80,0.58)*shadow;
#endif
    float block=pow(lm.x,3.0)*0.95;
    vec3 ambient=ambientRadiance(m.normal,lm.y)*m.ao;
    vec3 blockColor=vec3(1.0,0.63,0.32)*seasonAmbientTint();
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
