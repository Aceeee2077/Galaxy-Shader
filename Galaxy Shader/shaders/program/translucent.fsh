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
        float rain=weatherRainAmount();
        float storm=weatherStormAmount();
        float surfaceRoughness=0.020 + rain*(0.055+storm*0.045) + WATER_WAVES*0.008;
        vec2 refrUV=clamp(uv+(mat3(gbufferModelView)*n).xy*surfaceRoughness*
                   min(thickness,6.0)*1.35/(1.0+length(view)*0.012),pixelSize(),1.0-pixelSize());
        float rd=texture2D(depthtex1,refrUV).r;
        if(skyDepth(rd)<0.5 && length(viewPosition(refrUV,rd))<length(view)+0.05) refrUV=uv;
        vec3 behind=texture2D(colortex4,refrUV).rgb;
        float behindWeight=1.0;
#if WATER_QUALITY > 0
        // Rough water spreads the refracted background instead of leaving a
        // clean image. Rain and wind strongly increase this underwater blur.
        vec2 blurRadius=(0.6 + rain*2.8 + storm*1.2 + WATER_WAVES*0.6)*pixelSize()*
                        (0.5+thickness*0.22);
        int taps=min(WATER_QUALITY+2,5);
        for(int i=1;i<5;++i) {
            if(i>=taps) break;
            vec2 suv=clamp(refrUV+diskSample(i,taps)*blurRadius,pixelSize(),1.0-pixelSize());
            float sd=texture2D(depthtex1,suv).r;
            if(skyDepth(sd)<0.5 && length(viewPosition(suv,sd))<length(view)+max(thickness,2.0)) {
                behind+=texture2D(colortex4,suv).rgb;
                behindWeight+=1.0;
            }
        }
        behind/=behindWeight;
#endif
        float turbidity=rain*(0.55+storm*0.45);
        vec3 absorb=exp(-vec3(0.34,0.10,0.055)*(thickness*(1.0+turbidity*1.6))*FOG_DENSITY);
        vec3 biome=mix(vec3(0.018,0.09,0.11),toLinear(vColor.rgb)*0.22,0.35);
        vec3 waterLight=ambientRadiance(vec3(0,1,0),vLight.y)+directionalRadiance()*0.12;
        vec3 transmission=behind*absorb+biome*waterLight*(1.0-absorb);
        transmission=mix(transmission,biome*0.85,turbidity*0.45);
        float fresnel=0.02+0.98*pow(1.0-sat(dot(n,safeNormalize(-vPlayer))),5.0);
        fresnel=sat(fresnel+rain*0.10+storm*rain*0.05);
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
        float shore=1.0-smoothstep(0.0,1.8,thickness);
        if(shore>0.0) {
            vec2 foamPos=(vPlayer.xz+cameraPosition.xz)*1.7+weatherWindDirection()*frameTimeCounter*0.6;
            float foamNoise=fbm(foamPos,3);
            float foamBand=shore*smoothstep(0.42,0.78,foamNoise)*
                           (0.55+0.45*sin(thickness*9.0-frameTimeCounter*2.2));
            color=mix(color,vec3(0.72,0.80,0.82),sat(foamBand*0.60));
        }
        // The opaque background has already been transmitted exactly once.
        gl_FragData[0]=vec4(max(color,vec3(0)),1.0);
        return;
    }
    Material m=defaultMaterial(toLinear(tex.rgb),n);
    vec3 color=shadeSurface(m,vPlayer,vLight,vId);
    gl_FragData[0]=vec4(max(color,vec3(0)),tex.a);
}
