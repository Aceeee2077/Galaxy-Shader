varying float vCloudShadow;
#include "/lib/common.glsl"
#include "/lib/lighting.glsl"
uniform sampler2D texture, normals, specular;
uniform vec4 entityColor;
uniform float alphaTestRef;
varying vec2 vTex, vLight;
varying vec4 vColor;
varying vec3 vPlayer, vNormal, vTangent, vBitangent;
varying float vId;
/* DRAWBUFFERS:0123 */
void main() {
    vec4 tex=texture2D(texture,vTex)*vColor;
#ifdef TERRAIN
    // separateAo puts terrain occlusion in vertex alpha, not opacity.
    tex.a=texture2D(texture,vTex).a;
#endif
#ifdef BASIC
    tex=vColor;
#endif
    if(tex.a<max(alphaTestRef,0.001)) discard;
#ifdef ENTITY
    tex.rgb=mix(tex.rgb,entityColor.rgb,entityColor.a);
#endif
    Material m=defaultMaterial(toLinear(tex.rgb),safeNormalize(vNormal));
#if PBR_MODE == 2 || (PBR_MODE == 1 && defined(MC_TEXTURE_FORMAT_LAB_PBR))
#if defined(TERRAIN) || defined(BLOCK_ENTITY)
    if(dot(vTangent,vTangent)>0.5) {
        decodeLabPBR(m,texture2D(normals,vTex),texture2D(specular,vTex),
                     mat3(safeNormalize(vTangent),safeNormalize(vBitangent),m.normal));
    }
#endif
#endif
#ifdef TERRAIN
    m.ao*=vColor.a;
#endif
    if(vId>=10101.0 && vId<=10106.0) {
        // Preserve the atlas silhouette; only bright texels become incandescent.
        float bright=smoothstep(0.20,0.75,max(tex.r,max(tex.g,tex.b)));
        m.emission=max(m.emission,bright*0.8);
        m.albedo=mix(m.albedo,m.albedo*emissionTint(vId)*1.6,bright*0.45);
    }
#ifdef EMISSIVE
    m.emission=max(m.emission,0.8);
#endif
#if WET_SURFACES == 1 && DIMENSION == 0
    float wet=wetness*smoothstep(0.85,0.98,vLight.y)*max(m.normal.y,0.0);
    m.albedo*=1.0-0.22*wet;
    m.roughness=mix(m.roughness,min(m.roughness,0.18),wet*0.75);
#endif
    vec3 color=shadeSurface(m,vPlayer,vLight,vId);
    float hand=0.0;
#ifdef HAND
    hand=1.0;
#endif
    gl_FragData[0]=vec4(color,tex.a);
    gl_FragData[1]=vec4(m.normal*0.5+0.5,m.roughness);
    gl_FragData[2]=vec4(m.albedo,m.metal>0.5 ? -1.0 : m.f0.r);
    gl_FragData[3]=vec4(vLight.y,m.emission,hand,1.0);
}
