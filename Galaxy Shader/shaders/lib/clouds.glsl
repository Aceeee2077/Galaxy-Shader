#ifndef SE_CLOUDS
#define SE_CLOUDS
#include "/lib/cloud_field.glsl"
#include "/lib/atmosphere.glsl"
vec3 skyWithClouds(vec3 ray, vec3 origin, bool disks) {
    vec3 sky = atmosphere(ray,disks);
#if DIMENSION == 0 && CLOUD_QUALITY > 0
    float cloudHeight = 280.0;
    float t = (cloudHeight-origin.y)/(abs(ray.y)<0.005 ? 0.005 : ray.y);
    if (t>0.0 && t<18000.0) {
        vec2 p = origin.xz+ray.xz*t;
        float density = cloudDensity(p);
        float neighbor = cloudDensity(p+sunDirection().xz*55.0);
        float silver = sat(density-neighbor)*2.0;
        vec3 lit = mix(vec3(0.028,0.034,0.046)*NIGHT_BRIGHTNESS,
                       mix(vec3(0.45),sunlightColor()*0.85,0.65),dayAmount());
        float overcast=weatherOvercastAmount();
        vec3 stormCloud=mix(vec3(0.18,0.22,0.28),vec3(0.075,0.090,0.12),weatherStormAmount());
        lit=mix(lit,stormCloud,overcast*0.78);
        lit *= (0.70+0.4*silver)*(1.0-0.34*weatherStormAmount());
        lit += lightningBoltPosition.w*vec3(0.58,0.68,0.86)*
               density*(0.35+0.65*weatherStormAmount());
        float alpha = density*smoothstep(0.0,0.12,abs(ray.y))*exp(-t/18000.0);
        sky = mix(sky,lit,alpha);
    }
#endif
    return sky;
}
#endif
