#ifndef SE_REFLECTIONS
#define SE_REFLECTIONS
#include "/lib/clouds.glsl"
uniform sampler2D depthtex1;
vec4 traceReflection(sampler2D scene, vec3 view, vec3 worldNormal, float roughness) {
    vec3 n=safeNormalize(mat3(gbufferModelView)*worldNormal);
    vec3 direction=reflect(safeNormalize(view),n);
    vec3 start=view+n*0.12;
    vec4 result=vec4(0.0);
#if SSR_QUALITY > 0
    if(roughness>0.65) return result;
    int count=SSR_QUALITY*12;
    float previousT=0.1;
    for(int i=0;i<48;++i) {
        if(i>=count) break;
        float t=0.18+pow((float(i)+1.0)/float(count),1.6)*64.0;
        vec3 p=start+direction*t;
        if(p.z>=-near) break;
        vec2 uv=projectView(p);
        if(screenInside(uv)<0.5) break;
        float d=texture2D(depthtex1,uv).r;
        if(skyDepth(d)>0.5) { previousT=t; continue; }
        float sceneZ=viewPosition(uv,d).z;
        float delta=sceneZ-p.z;
        if(delta>0.0 && delta<0.3+(t-previousT)*abs(direction.z)*1.5 && t>0.5) {
            float lo=previousT, hi=t;
            for(int j=0;j<5;++j) {
                float mid=(lo+hi)*0.5;
                vec3 mp=start+direction*mid;
                vec2 mu=projectView(mp);
                float md=texture2D(depthtex1,mu).r;
                if(skyDepth(md)<0.5 && viewPosition(mu,md).z>mp.z) hi=mid; else lo=mid;
            }
            vec3 hit=start+direction*hi;
            uv=projectView(hit);
            float hitDepth=texture2D(depthtex1,uv).r;
            if(skyDepth(hitDepth)>0.5 || abs(viewPosition(uv,hitDepth).z-hit.z)>0.7) break;
            float edge=smoothstep(0.0,0.08,min(min(uv.x,uv.y),min(1.0-uv.x,1.0-uv.y)));
            result=vec4(texture2D(scene,uv).rgb,edge*(1.0-smoothstep(0.15,0.65,roughness)));
            break;
        }
        previousT=t;
    }
#endif
    return result;
}
vec3 environmentReflection(vec3 player, vec3 n, float roughness, float skyLight) {
    vec3 ray=reflect(safeNormalize(player),n);
    vec3 env=skyWithClouds(ray,player+cameraPosition,false);
    env=mix(env,atmosphere(vec3(0,1,0),false),roughness*0.6);
    return env*mix(0.04,1.0,skyLight*skyLight);
}
#endif
