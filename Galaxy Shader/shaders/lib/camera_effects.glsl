#ifndef SE_CAMERA_EFFECTS
#define SE_CAMERA_EFFECTS
#include "/lib/noise.glsl"
uniform sampler2D colortex0, colortex3, depthtex0;
vec3 cameraEffects(vec2 uv) {
    vec3 color=texture2D(colortex0,uv).rgb;
    if(texture2D(colortex3,uv).b>0.5) return color;
#if DOF_QUALITY > 0
    float d=texture2D(depthtex0,uv).r;
    float z=length(viewPosition(uv,d));
    float focus=max(-viewPosition(vec2(0.5),centerDepthSmooth).z,0.3);
    float coc=min(abs(z-focus)/max(z,0.1)*float(DOF_QUALITY)*2.0,8.0);
    vec3 sum=color; float total=1.0;
    int count=DOF_QUALITY*6;
    for(int i=0;i<18;++i) {
        if(i>=count) break;
        vec2 suv=clamp(uv+diskSample(i,count)*pixelSize()*coc,0.0,1.0);
        if(texture2D(colortex3,suv).b>0.5) continue;
        float sz=length(viewPosition(suv,texture2D(depthtex0,suv).r));
        float w=1.0-smoothstep(0.03,0.18,abs(sz-z)/max(z,0.1));
        sum+=texture2D(colortex0,suv).rgb*w; total+=w;
    }
    color=sum/total;
#endif
#if MOTION_BLUR > 0
    float depth=texture2D(depthtex0,uv).r;
    if(skyDepth(depth)<0.5 && distance(cameraPosition,previousCameraPosition)<8.0) {
        vec3 player=playerPosition(viewPosition(uv,depth));
        vec4 previous=gbufferPreviousProjection*gbufferPreviousModelView*
                      vec4(player+cameraPosition-previousCameraPosition,1.0);
        if(previous.w>0.0) {
            vec2 velocity=uv-(previous.xy/previous.w*0.5+0.5);
            velocity*=min(1.0,0.035/max(length(velocity),0.0001));
            vec3 accum=color; float weight=1.0;
            int count=MOTION_BLUR*4;
            for(int i=1;i<12;++i) {
                if(i>=count) break;
                vec2 suv=uv-velocity*(float(i)/float(count)-0.5)*0.5;
                if(screenInside(suv)<0.5 || texture2D(colortex3,suv).b>0.5) continue;
                float sd=texture2D(depthtex0,suv).r;
                float z=-viewPosition(uv,depth).z, sz=-viewPosition(suv,sd).z;
                if(abs(sz-z)>max(0.2,z*0.08)) continue;
                accum+=texture2D(colortex0,suv).rgb; weight+=1.0;
            }
            color=accum/weight;
        }
    }
#endif
    return color;
}
#endif
