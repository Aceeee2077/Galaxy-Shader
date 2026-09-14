#ifndef SE_ATMOSPHERE
#define SE_ATMOSPHERE
#include "/lib/noise.glsl"
#include "/lib/end_sky.glsl"
#include "/lib/weather.glsl"
vec3 sunlightColor() {
    float h = max(sunDirection().y,0.0);
    return mix(vec3(1.0,0.32,0.10),vec3(1.0,0.95,0.85),smoothstep(0.0,0.4,h));
}
vec3 directionalRadiance() {
    float d = dayAmount();
    float horizon = smoothstep(0.0,0.12,abs(sunDirection().y));
    vec3 sun = sunlightColor() * (2.8*SUN_INTENSITY);
    float phase = 0.45 + 0.55 * abs(float(moonPhase)-4.0)/4.0;
    vec3 moon = vec3(0.12,0.15,0.20)*NIGHT_BRIGHTNESS*phase;
    return mix(moon,sun,d)*horizon*(1.0-0.64*weatherRainAmount())*
           (1.0-0.42*weatherStormAmount());
}
vec3 atmosphere(vec3 ray, bool disks) {
#if DIMENSION == -1
    float ash = fbm(ray.xz*4.0+frameTimeCounter*0.005,3);
    return mix(toLinear(fogColor)*0.9,vec3(0.12,0.024,0.008),0.4)+ash*vec3(0.018,0.006,0.002);
#elif DIMENSION == 1
    return endCosmos(ray,disks);
#else
    vec3 sun = sunDirection();
    float day = dayAmount(), mu = dot(ray,sun);
    float h = max(ray.y,0.0);
    float optical = 1.0/(0.18+pow(h,0.6));
    vec3 betaR = vec3(0.19,0.40,0.83);
    vec3 transmit = exp(-betaR*optical*0.28);
    float rayleigh = 0.75*(1.0+mu*mu);
    float g = 0.76;
    float mie = (1.0-g*g)/pow(max(1.0+g*g-2.0*g*mu,0.08),1.5);
    vec3 scatter = (1.0-transmit)*vec3(0.48,0.64,0.90)*rayleigh;
    scatter += sunlightColor()*mie*0.012*smoothstep(-0.12,0.1,sun.y);
    float sunset = (1.0-smoothstep(0.03,0.35,abs(sun.y)))*smoothstep(-0.15,0.0,sun.y);
    scatter += vec3(0.52,0.12,0.035)*sunset*pow(1.0-h,4.0)*(0.25+0.75*pow(max(mu,0.0),3.0));
    vec3 night = mix(vec3(0.006,0.009,0.018),vec3(0.018,0.023,0.037),pow(1.0-h,3.0))*NIGHT_BRIGHTNESS;
    vec3 sky = mix(night,scatter,day);
    float overcast=weatherOvercastAmount();
    vec3 cloudySky=mix(vec3(0.16,0.20,0.25),vec3(0.055,0.070,0.095),weatherStormAmount());
    cloudySky*=mix(0.42,1.0,day);
    sky=mix(sky,cloudySky,overcast*0.74);
    sky *= 1.0-0.22*weatherStormAmount();
    if (disks && ray.y>-0.02) {
        sky += sunlightColor()*14.0*smoothstep(0.99988,0.99996,mu)*day*(1.0-overcast);
        vec3 moon = worldDirection(moonPosition);
        sky += vec3(1.2,1.3,1.5)*smoothstep(0.99976,0.99994,dot(ray,moon))*(1.0-day)*(1.0-overcast);
        vec2 starUV = vec2(atan(ray.z,ray.x),asin(clamp(ray.y,-1.0,1.0)))*vec2(700.0,900.0);
        float star = step(0.996,hash12(floor(starUV)))*pow(max(1.0-length(fract(starUV)-0.5)*2.0,0.0),4.0);
        sky += vec3(star*0.7*(1.0-day)*(1.0-overcast)*smoothstep(0.0,0.2,ray.y));
    }
    sky += lightningBoltPosition.w*vec3(0.24,0.30,0.43)*(0.45+0.55*weatherStormAmount());
    return max(sky,vec3(0.0));
#endif
}
#endif
