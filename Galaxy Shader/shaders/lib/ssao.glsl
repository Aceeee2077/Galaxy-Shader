#ifndef SE_SSAO
#define SE_SSAO
#include "/lib/noise.glsl"
uniform sampler2D colortex0, colortex1, colortex2, colortex3;
vec4 screenIndirect(vec2 uv, vec3 view, vec3 worldNormal) {
    vec3 bounce=vec3(0.0);
    float occlusion=0.0, weight=0.0;
#if AO_QUALITY > 0 || INDIRECT_QUALITY > 0
    vec3 n=safeNormalize(mat3(gbufferModelView)*worldNormal);
    int count=max(AO_QUALITY*4,INDIRECT_QUALITY*4);
    float radius=1.25;
    vec2 radiusUV=vec2(gbufferProjection[0][0],gbufferProjection[1][1])*radius/max(-view.z,1.0)*0.5;
    radiusUV=min(radiusUV,vec2(0.12));
    for(int i=0;i<16;++i) {
        if(i>=count) break;
        vec2 suv=uv+diskSample(i,count)*radiusUV;
        if(screenInside(suv)<0.5) continue;
        float depth=texture2D(depthtex1,suv).r;
        if(skyDepth(depth)>0.5) continue;
        vec4 meta=texture2D(colortex3,suv);
        if(meta.a<0.5 || meta.b>0.5) continue;
        vec3 delta=viewPosition(suv,depth)-view;
        float dist=length(delta);
        vec3 dir=delta/max(dist,0.001);
        float range=1.0-smoothstep(radius*0.25,radius,dist);
        float facing=max(dot(n,dir)-0.08,0.0);
        occlusion+=facing*range;
#if INDIRECT_QUALITY > 0
        vec3 otherNormal=safeNormalize(mat3(gbufferModelView)*(texture2D(colortex1,suv).xyz*2.0-1.0));
        float exchange=max(dot(otherNormal,-dir),0.0)*facing*range;
        bounce+=min(texture2D(colortex0,suv).rgb,vec3(3.0))*exchange;
#endif
        weight+=1.0;
    }
    occlusion/=max(weight,1.0);
    bounce/=max(weight,1.0);
#endif
#if AO_QUALITY == 0
    occlusion=0.0;
#endif
    return vec4(bounce*(0.12*float(INDIRECT_QUALITY)),1.0-min(occlusion*0.75,0.35));
}
#endif
