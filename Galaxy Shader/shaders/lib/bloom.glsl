#ifndef SE_BLOOM
#define SE_BLOOM
vec3 brightPass(vec3 c) {
    float lum=luminance(c);
    // Continuous soft knee: small luminous surfaces bloom before clipping,
    // while ordinary diffuse surfaces stay below the shoulder.
    float knee=clamp(lum-0.75,0.0,1.0);
    float contribution=max(lum-1.25,knee*knee*0.25);
    return min(c*(contribution/max(lum,0.0001)),vec3(8.0));
}
vec3 gaussianBlur(sampler2D source, vec2 uv, vec2 direction) {
    vec3 c=texture2D(source,uv).rgb*0.227027;
    c+=(texture2D(source,uv+direction*1.384615).rgb+texture2D(source,uv-direction*1.384615).rgb)*0.316216;
    c+=(texture2D(source,uv+direction*3.230769).rgb+texture2D(source,uv-direction*3.230769).rgb)*0.070270;
    return c;
}
vec3 gaussianBlurLow(sampler2D source, vec2 uv, vec2 direction) {
    // Three taps with normalized weights. A constant field keeps its exact
    // value, so the low profile saves two fetches per blur pass without
    // changing the overall bloom energy.
    return texture2D(source,uv).rgb*0.5+
           (texture2D(source,uv+direction).rgb+texture2D(source,uv-direction).rgb)*0.25;
}
#endif
