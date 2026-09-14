varying float vCloudShadow;
#include "/lib/common.glsl"
#include "/lib/lighting.glsl"
#include "/lib/reflections.glsl"
#include "/lib/water.glsl"
uniform sampler2D texture, colortex4;
uniform float alphaTestRef;
varying vec2 vTex, vLight;
varying vec4 vColor;
varying vec3 vPlayer, vNormal, vTangent, vBitangent;
varying float vId;
/* DRAWBUFFERS:0 */
void main() {
    vec4 tex=texture2D(texture,vTex)*vColor;
    if(tex.a<0.001) discard;
    vec3 n=safeNormalize(vNormal);
    if(abs(vId-10000.0)<0.5) {
        vec2 uv=gl_FragCoord.xy*pixelSize();
        vec3 view=(gbufferModelView*vec4(vPlayer,1.0)).xyz;
        float d=texture2D(depthtex1,uv).r;
        float thickness=skyDepth(d)>0.5 ? 32.0 : max(length(viewPosition(uv,d))-length(view),0.0);
        n=waterNormal(vPlayer+cameraPosition,n,length(vPlayer));
        if(dot(n,-vPlayer)<0.0) n=-n;
        vec2 offset=(mat3(gbufferModelView)*n).xy*0.018*min(thickness,2.0)/(1.0+length(view)*0.015);
        vec2 refrUV=clamp(uv+offset,pixelSize(),1.0-pixelSize());
        float rd=texture2D(depthtex1,refrUV).r;
        if(skyDepth(rd)<0.5 && length(viewPosition(refrUV,rd))<length(view)+0.05) refrUV=uv;
        vec3 behind=texture2D(colortex4,refrUV).rgb;
        vec3 absorb=exp(-vec3(0.28,0.085,0.045)*thickness);
        vec3 biome=mix(vec3(0.018,0.09,0.11),toLinear(vColor.rgb)*0.22,0.35);
        vec3 waterLight=ambientRadiance(vec3(0,1,0),vLight.y)+directionalRadiance()*0.12;
        vec3 transmission=behind*absorb+biome*waterLight*(1.0-absorb);
        float fresnel=0.02+0.98*pow(1.0-sat(dot(n,safeNormalize(-vPlayer))),5.0);
        fresnel=sat(fresnel+weatherStormAmount()*weatherRainAmount()*0.035);
        vec3 env=environmentReflection(vPlayer,n,0.07,vLight.y);
        vec4 ssr=traceReflection(colortex4,view,n,0.07);
        Material m=defaultMaterial(toLinear(tex.rgb),n);
        m.normal=n; m.f0=vec3(0.02); m.roughness=mix(0.075,0.055,weatherStormAmount());
        vec3 spec=vec3(0.0);
#if DIMENSION == 0
        spec=specularBRDF(m,safeNormalize(-vPlayer),lightDirection())*directionalRadiance()*
             shadowVisibility(vPlayer,n,true)*smoothstep(0.05,0.4,vLight.y);
#endif
        vec3 stormHighlight=lightningBoltPosition.w*vec3(0.42,0.56,0.82)*
                            (0.25+0.75*fresnel)*weatherRainAmount();
        vec3 color=mix(transmission,mix(env,ssr.rgb,ssr.a),fresnel)+spec+stormHighlight;
        color=mix(behind,color,smoothstep(0.0,0.18,thickness));
        // The opaque background has already been transmitted exactly once.
        gl_FragData[0]=vec4(max(color,vec3(0)),1.0);
        return;
    }
    Material m=defaultMaterial(toLinear(tex.rgb),n);
    vec3 color=shadeSurface(m,vPlayer,vLight,vId);
    gl_FragData[0]=vec4(max(color,vec3(0)),tex.a);
}
