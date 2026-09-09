uniform sampler2D texture;
varying vec2 vTex;
varying float vId;
/* DRAWBUFFERS:0 */
void main() {
    if(vId==10000.0 || vId==10010.0) discard;
    if(texture2D(texture,vTex).a<0.1) discard;
    gl_FragData[0]=vec4(1.0);
}
