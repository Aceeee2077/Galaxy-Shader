#include "/lib/common.glsl"
#include "/lib/wind.glsl"
attribute vec4 mc_Entity;
attribute vec4 mc_midTexCoord;
varying vec2 vTex;
varying float vId;
void main() {
    vec4 shadowView=gl_ModelViewMatrix*gl_Vertex;
    vec3 player=(shadowModelViewInverse*shadowView).xyz;
    float upper=gl_MultiTexCoord0.t<mc_midTexCoord.t ? 1.0 : 0.0;
    if(mc_Entity.x==10004.0) upper=1.0;
    player+=vegetationWind(player+cameraPosition,mc_Entity.x,upper);
    gl_Position=gl_ProjectionMatrix*shadowModelView*vec4(player,1.0);
    vTex=(gl_TextureMatrix[0]*gl_MultiTexCoord0).xy;
    vId=mc_Entity.x;
}
