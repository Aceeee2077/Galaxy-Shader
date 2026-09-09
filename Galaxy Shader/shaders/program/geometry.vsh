#include "/lib/common.glsl"
#include "/lib/wind.glsl"
#include "/lib/cloud_field.glsl"
attribute vec4 mc_Entity;
attribute vec4 at_tangent;
attribute vec4 mc_midTexCoord;
uniform int entityId, blockEntityId, currentRenderedItemId;
varying vec2 vTex, vLight;
varying vec4 vColor;
varying vec3 vPlayer, vNormal, vTangent, vBitangent;
varying float vId;
varying float vCloudShadow;
void main() {
    vec4 view=gl_ModelViewMatrix*gl_Vertex;
    vec3 player=playerPosition(view.xyz);
    vId=0.0;
#ifdef TERRAIN
    vId=mc_Entity.x;
    float upper=gl_MultiTexCoord0.t<mc_midTexCoord.t ? 1.0 : 0.0;
    // Upper half of tall plants is fully mobile, including its lower vertices.
    if(vId==10004.0) upper=1.0;
    player+=vegetationWind(player+cameraPosition,vId,upper);
    view=gbufferModelView*vec4(player,1.0);
#endif
#ifdef ENTITY
    vId=float(entityId);
#endif
#ifdef BLOCK_ENTITY
    vId=float(blockEntityId);
#endif
#ifdef HAND
    vId=float(currentRenderedItemId);
#endif
    gl_Position=gl_ProjectionMatrix*view;
    vPlayer=player;
    vCloudShadow=cloudShadow(player+cameraPosition);
    vNormal=worldDirection(gl_NormalMatrix*gl_Normal);
    vTangent=worldDirection(gl_NormalMatrix*at_tangent.xyz);
    vBitangent=safeNormalize(cross(vNormal,vTangent))*at_tangent.w;
    vTex=(gl_TextureMatrix[0]*gl_MultiTexCoord0).xy;
    vLight=clamp((gl_TextureMatrix[1]*gl_MultiTexCoord1).xy*(256.0/240.0)-vec2(8.0/240.0),0.0,1.0);
    vColor=gl_Color;
}
