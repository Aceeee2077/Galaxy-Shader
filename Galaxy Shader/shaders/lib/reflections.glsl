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
    if(roughness>0.62 || direction.z>0.05) return result;
#if SSR_QUALITY == 1
    const int count=12;
    const float maxDistance=36.0;
#elif SSR_QUALITY == 2
    const int count=20;
    const float maxDistance=52.0;
#elif SSR_QUALITY == 3
    const int count=28;
    const float maxDistance=64.0;
#else
    const int count=40;
    const float maxDistance=80.0;
#endif
    float previousT=0.08;
    float t=previousT;
    for(int i=0;i<count;++i) {
        float progress=(float(i)+1.0)/float(count);
        // Small near-camera steps retain contact; steps grow with travel distance.
        t+=mix(0.10,maxDistance/float(count)*2.1,progress*progress);
        if(t>maxDistance) break;
        vec3 p=start+direction*t;
        if(p.z>=-near) break;
        vec2 uv=projectView(p);
        if(screenInside(uv)<0.5) break;
        float d=texture2D(depthtex1,uv).r;
        if(skyDepth(d)>0.5) { previousT=t; continue; }
        float sceneZ=viewPosition(uv,d).z;
        float delta=sceneZ-p.z;
        float thickness=(0.10+t*0.006)+(t-previousT)*abs(direction.z)*0.9;
        if(delta>0.0 && delta<thickness && t>0.35) {
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
            float hitError=abs(viewPosition(uv,hitDepth).z-hit.z);
            if(skyDepth(hitDepth)>0.5 || hitError>thickness*1.5) break;
            float edge=smoothstep(0.0,0.08,min(min(uv.x,uv.y),min(1.0-uv.x,1.0-uv.y)));
            float depthConfidence=1.0-smoothstep(thickness*0.25,thickness*1.5,hitError);
            float angleConfidence=smoothstep(0.02,0.35,abs(dot(n,direction)));
            float distanceConfidence=1.0-smoothstep(maxDistance*0.55,maxDistance,t);
            float roughnessConfidence=1.0-smoothstep(0.15,0.62,roughness);
            vec2 blur=pixelSize()*(1.0+roughness*8.0);
            vec3 reflected=texture2D(scene,uv).rgb;
            if(roughness>0.15) {
                reflected*=0.40;
                reflected+=(texture2D(scene,uv+vec2(blur.x,0)).rgb+
                            texture2D(scene,uv-vec2(blur.x,0)).rgb+
                            texture2D(scene,uv+vec2(0,blur.y)).rgb+
                            texture2D(scene,uv-vec2(0,blur.y)).rgb)*0.15;
            }
            float confidence=edge*depthConfidence*angleConfidence*
                             distanceConfidence*roughnessConfidence;
            result=vec4(reflected,confidence);
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
