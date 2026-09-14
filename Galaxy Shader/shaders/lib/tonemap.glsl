#ifndef SE_TONEMAP
#define SE_TONEMAP
vec3 legacyFilmic(vec3 x) {
    // A bounded rational film response, applied only after exposure and HDR effects.
    vec3 a=x*(2.51*x+0.03);
    vec3 b=x*(2.43*x+0.59)+0.14;
    return clamp(a/b,0.0,1.0);
}
vec3 acesLike(vec3 x) {
    // Slightly softer shoulder than the legacy fit, preserving dark midtones.
    x=max(x,vec3(0.0));
    return clamp((x*(2.30*x+0.035))/(x*(2.18*x+0.58)+0.14),0.0,1.0);
}
vec3 agxLike(vec3 x) {
    // Luminance-domain log encoding and a smooth sigmoid approximate AgX's
    // wide highlight shoulder without depending on a LUT or color extension.
    x=max(x,vec3(0.0));
    float lum=max(luminance(x),1e-6);
    float encoded=clamp((log2(lum)+10.0)/16.0,0.0,1.0);
    float shaped=encoded*encoded*(3.0-2.0*encoded);
    shaped=pow(shaped,1.18);
    vec3 mapped=x*(shaped/lum);
    float highlight=smoothstep(0.55,1.0,shaped);
    mapped=mix(mapped,vec3(luminance(mapped)),highlight*0.12);
    return clamp(mapped,0.0,1.0);
}
float adaptedExposure() {
    float gain=1.0;
#if AUTO_EXPOSURE == 1
    float sky=sat(float(eyeBrightnessSmooth.y)/240.0);
    float block=sat(float(eyeBrightnessSmooth.x)/240.0);
    float illumination=max(sky*mix(0.16,1.0,dayAmount()),block*0.45);
    // Iris smooths the eye lightmap over time; bounded gain keeps caves dark.
    gain=mix(1.38,0.94,sqrt(illumination));
#endif
    return gain*EXPOSURE;
}
vec3 gradeColor(vec3 hdr) {
    vec3 exposed=max(hdr,vec3(0))*adaptedExposure();
#if TONEMAP_MODE == 0
    vec3 c=legacyFilmic(exposed);
#elif TONEMAP_MODE == 1
    vec3 c=acesLike(exposed);
#else
    vec3 c=agxLike(exposed);
#endif
    // Very mild white balance: nights remain readable without a blue/purple cast.
    vec3 balance=mix(vec3(1.025,1.0,0.965),vec3(1.0),dayAmount());
    c*=balance;
    c=mix(vec3(luminance(c)),c,SATURATION);
    c=(c-0.5)*CONTRAST+0.5;
    return pow(clamp(c,0.0,1.0),vec3(1.0/2.2));
}
#endif
