#ifndef SE_BLOOM
#define SE_BLOOM
vec3 brightPass(vec3 c) {
    float lum=luminance(c);
    float knee=sat((lum-0.8)/0.5);
    return c*(max(lum-1.3,0.0)+knee*knee*0.15)/max(lum,0.0001);
}
vec3 gaussianBlur(sampler2D source, vec2 uv, vec2 direction) {
    vec3 c=texture2D(source,uv).rgb*0.227027;
    c+=(texture2D(source,uv+direction*1.384615).rgb+texture2D(source,uv-direction*1.384615).rgb)*0.316216;
    c+=(texture2D(source,uv+direction*3.230769).rgb+texture2D(source,uv-direction*3.230769).rgb)*0.070270;
    return c;
}
#endif
