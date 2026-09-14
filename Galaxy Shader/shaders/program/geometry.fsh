varying float vCloudShadow;
#include "/lib/common.glsl"
#include "/lib/lighting.glsl"
#include "/lib/weather.glsl"
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
    float rainSplash=0.0;
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
    float foliage=step(10000.5,vId)*step(vId,10005.5);
    float upward=mix(max(m.normal.y,0.0),0.58+0.42*max(m.normal.y,0.0),foliage);
    float exposure=smoothstep(0.78,0.98,vLight.y)*upward;
    float wet=weatherWetness()*exposure;
    m.albedo*=1.0-0.25*wet;
    m.roughness=mix(m.roughness,min(m.roughness,0.10),wet*0.86);
#if WEATHER_QUALITY > 0
    float activeRain=weatherRainAmount()*exposure;
    if(activeRain>0.001) {
        vec3 impact=rainRippleField(vPlayer.xz+cameraPosition.xz,2.8);
        m.normal=safeNormalize(m.normal+vec3(impact.x,0.0,impact.y)*activeRain*0.028*RIPPLE_STRENGTH);
        rainSplash=pow(impact.z,2.5)*activeRain*RIPPLE_STRENGTH;
    }
#endif
#endif
    vec3 color=shadeSurface(m,vPlayer,vLight,vId);
#if WET_SURFACES == 1 && DIMENSION == 0
    vec3 splashLight=mix(vec3(0.08,0.10,0.13),sunlightColor(),dayAmount());
    splashLight+=lightningBoltPosition.w*vec3(0.65,0.78,1.0);
    color+=splashLight*rainSplash*0.038;
#endif
    float hand=0.0;
#ifdef HAND
    hand=1.0;
#endif
    gl_FragData[0]=vec4(color,tex.a);
    gl_FragData[1]=vec4(m.normal*0.5+0.5,m.roughness);
    gl_FragData[2]=vec4(m.albedo,m.metal>0.5 ? -1.0 : m.f0.r);
    gl_FragData[3]=vec4(vLight.y,m.emission,hand,1.0);
}
