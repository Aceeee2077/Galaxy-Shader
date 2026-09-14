#ifndef SE_WATER
#define SE_WATER
#include "/lib/weather.glsl"
vec3 waterNormal(vec3 world, vec3 geometric, float distanceToEye) {
    float t=frameTimeCounter;
    vec2 gradient=vec2(0.0);
#if WATER_QUALITY > 0
    for(int i=0;i<4;++i) {
        if(i>WATER_QUALITY) break;
        float fi=float(i);
        vec2 dir=vec2(cos(fi*2.17+0.2),sin(fi*2.17+0.2));
        float frequency=0.8+fi*1.6;
        float amplitude=0.065/(1.0+fi);
        gradient+=dir*cos(dot(world.xz,dir)*frequency+t*(1.1+fi*0.37))*amplitude;
    }
    float rain=weatherRainAmount();
    if(rain>0.001) {
        vec3 ripple=rainRippleField(world.xz,1.35);
        gradient+=ripple.xy*rain*RIPPLE_STRENGTH*0.052;
        vec2 wind=weatherWindDirection();
        gradient+=wind*sin(dot(world.xz,wind)*13.0-t*(5.0+weatherStormAmount()*4.0))*
                  rain*(0.012+weatherStormAmount()*0.014);
    }
#endif
    gradient*=WATER_WAVES/(1.0+distanceToEye*0.012);
    return safeNormalize(geometric+vec3(gradient.x,0,gradient.y)*abs(geometric.y));
}
#endif
