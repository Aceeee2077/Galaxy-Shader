#include "/lib/common.glsl"
#include "/lib/buffers.glsl"
#include "/lib/pbr.glsl"
#include "/lib/reflections.glsl"
#include "/lib/ssao.glsl"
varying vec2 texcoord;
/* DRAWBUFFERS:04 */
void main() {
    vec2 uv=texcoord;
    float d=texture2D(depthtex1,uv).r;
    vec3 view=viewPosition(uv,d);
    vec3 player=playerPosition(view);
    vec3 color=texture2D(colortex0,uv).rgb;
    if(skyDepth(d)>0.5) {
        color=skyWithClouds(worldDirection(view),cameraPosition,true);
    } else {
        vec4 meta=texture2D(colortex3,uv);
        if(meta.a>0.5 && meta.b<0.5) {
            vec4 nr=texture2D(colortex1,uv);
            vec3 n=safeNormalize(nr.xyz*2.0-1.0);
            vec4 indirect=screenIndirect(uv,view,n);
            color=color*indirect.a+indirect.rgb*texture2D(colortex2,uv).rgb;
            if(nr.a<0.65) {
                vec4 albedo=texture2D(colortex2,uv);
                vec3 f0=albedo.a<0.0 ? albedo.rgb : vec3(albedo.a);
                vec3 f=fresnelSchlick(f0,dot(n,safeNormalize(-player)));
                vec3 env=environmentReflection(player,n,nr.a,meta.r);
                vec4 ssr=traceReflection(colortex0,view,n,nr.a);
                color+=mix(env,ssr.rgb,ssr.a)*f*(1.0-nr.a*0.7);
            }
        }
    }
    gl_FragData[0]=vec4(max(color,vec3(0)),1.0);
    gl_FragData[1]=vec4(max(color,vec3(0)),1.0);
}
