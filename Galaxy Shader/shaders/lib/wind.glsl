#ifndef SE_WIND
#define SE_WIND
#include "/lib/noise.glsl"
vec3 vegetationWind(vec3 world, float id, float upper) {
#if DIMENSION == 0
    if (id>=10001.0 && id<=10005.0) {
        float time = frameTimeCounter;
        float anchor = id==10002.0 || id==10005.0 ? 0.4 : upper;
        float gust = valueNoise(world.xz*0.13+time*0.12);
        float phase = time*(1.8+rainStrength*0.4)+world.x*0.55+world.z*0.37;
        float a = sin(phase)+0.4*sin(phase*1.71+world.y);
        float strength = WIND_STRENGTH*(0.025+0.045*gust)*(1.0+rainStrength+thunderStrength)*anchor;
        return vec3(a,0.15*sin(phase*0.8),cos(phase*0.83))*strength;
    }
#endif
    return vec3(0.0);
}
#endif
