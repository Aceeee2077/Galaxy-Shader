#ifndef SE_TONEMAP
#define SE_TONEMAP
vec3 filmic(vec3 x) {
    // A bounded rational film response, applied only after exposure and HDR effects.
    vec3 a=x*(2.51*x+0.03);
    vec3 b=x*(2.43*x+0.59)+0.14;
    return clamp(a/b,0.0,1.0);
}
float adaptedExposure() {
    float gain=1.0;
#if AUTO_EXPOSURE == 1
    float sky=sat(float(eyeBrightnessSmooth.y)/240.0);
    float block=sat(float(eyeBrightnessSmooth.x)/240.0);
    float illumination=max(sky*mix(0.16,1.0,dayAmount()),block*0.45);
    // Iris smooths the eye lightmap over time; bounded gain keeps caves dark.
    gain=mix(1.60,0.95,sqrt(illumination));
#endif
    return gain*EXPOSURE;
}
vec3 gradeColor(vec3 hdr) {
    vec3 c=filmic(max(hdr,vec3(0))*adaptedExposure());
    c=mix(vec3(luminance(c)),c,SATURATION);
    c=(c-0.5)*CONTRAST+0.5;
    return pow(clamp(c,0.0,1.0),vec3(1.0/2.2));
}
#endif
