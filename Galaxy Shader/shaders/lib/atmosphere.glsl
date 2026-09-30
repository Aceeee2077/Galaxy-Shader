#ifndef SE_ATMOSPHERE
#define SE_ATMOSPHERE
#include "/lib/noise.glsl"
#include "/lib/end_sky.glsl"
#include "/lib/weather.glsl"
#include "/lib/night_sky.glsl"
#include "/lib/seasons.glsl"
#include "/lib/biome.glsl"
#include "/lib/celestial.glsl"
vec3 sunlightColor() {
    float h = max(sunDirection().y,0.0);
    return mix(vec3(1.0,0.49,0.19),vec3(1.0,0.95,0.85),smoothstep(0.0,0.4,h));
}
vec3 directionalRadiance() {
    float d = dayAmount();
    float horizon = smoothstep(0.0,0.12,abs(sunDirection().y));
    vec3 sun = sunlightColor() * (2.00*SUN_INTENSITY) * seasonSunTint();
    float phase = 0.45 + 0.55 * abs(float(moonPhase)-4.0)/4.0;
    vec3 moon = vec3(0.12,0.15,0.20)*NIGHT_BRIGHTNESS*phase*seasonSkyTint();
    return mix(moon,sun,d)*horizon*(1.0-0.64*weatherRainAmount())*
           (1.0-0.42*weatherStormAmount())*(1.0-0.88*eclipseAmount());
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
    scatter += vec3(0.72,0.34,0.10)*sunset*pow(1.0-h,2.5)*(0.35+0.65*pow(max(mu,0.0),3.0));
    vec3 night = mix(vec3(0.006,0.009,0.018),vec3(0.018,0.023,0.037),pow(1.0-h,3.0))*NIGHT_BRIGHTNESS;
    vec3 sky = mix(night,scatter,day);
    // Subtle daily variation keeps consecutive Minecraft days from looking identical.
    sky *= mix(0.94, 1.06, dayVariation()) * seasonSkyTint() * biomeSkyTint();
    float eclipse=eclipseAmount();
    sky *= 1.0-0.72*eclipse;
    float overcast=weatherOvercastAmount();
    vec3 cloudySky=mix(vec3(0.16,0.20,0.25),vec3(0.055,0.070,0.095),weatherStormAmount());
    cloudySky*=mix(0.42,1.0,day);
    // Low sunlight still colors rain clouds; midday and night retain cool storms.
    cloudySky=mix(cloudySky,vec3(0.40,0.31,0.17),sunset*0.72);
    sky=mix(sky,cloudySky,overcast*0.74);
    sky *= 1.0-0.22*weatherStormAmount();
    if (disks && ray.y>-0.02) {
        sky += sunlightColor()*14.0*smoothstep(0.99988,0.99996,mu)*day*(1.0-overcast)*(1.0-0.95*eclipse);
        sky += vec3(1.00,0.82,0.55)*exp(-pow((1.0-mu)*58.0,2.0))*eclipse*2.2;
        vec3 moon = worldDirection(moonPosition);
        sky += vec3(1.2,1.3,1.5)*smoothstep(0.99976,0.99994,dot(ray,moon))*(1.0-day)*(1.0-overcast);
        vec2 starUV = vec2(atan(ray.z,ray.x),asin(clamp(ray.y,-1.0,1.0)))*vec2(700.0,900.0);
        float star = step(0.996,hash12(floor(starUV)))*pow(max(1.0-length(fract(starUV)-0.5)*2.0,0.0),4.0);
        sky += vec3(star*0.7*(1.0-day)*(1.0-overcast)*smoothstep(0.0,0.2,ray.y));
#if COSMIC_SKY_QUALITY > 0
        float cosmicNight = (1.0-day)*(1.0-overcast*0.82);
        sky += galaxyNebula(ray)*cosmicNight*(0.55+0.45*float(COSMIC_SKY_QUALITY>=2));
#if COSMIC_SKY_QUALITY >= 2
        sky += auroraSky(ray,cosmicNight*biomeAuroraBoost()*(1.0+auroraStormAmount()*0.9));
        sky += shootingStars(ray)*cosmicNight*(1.0+meteorShowerAmount()*2.2);
        sky += cometSky(ray,cosmicNight);
        sky += supernovaSky(ray,cosmicNight);
#endif
#endif
    }
#if WEATHER_QUALITY > 0
    // A single ordered spectral arc around the anti-solar point. Iris wetness
    // lets it linger briefly after rain while direct daylight is returning.
    float rainbowMoisture = max(weatherRainAmount(), weatherWetness() * 0.72);
    if (rainbowMoisture > 0.025 && sun.y > 0.02 && ray.y > 0.0) {
        float angle = acos(clamp(dot(ray, -sun), -1.0, 1.0));
        float spectral = (angle - 0.655) / 0.145;
        if (spectral > 0.0 && spectral < 1.0) {
            float edge = smoothstep(0.0, 0.09, spectral) *
                         (1.0 - smoothstep(0.91, 1.0, spectral));
            vec3 bow = mix(vec3(0.40, 0.16, 0.74), vec3(0.10, 0.32, 0.95), smoothstep(0.06, 0.24, spectral));
            bow = mix(bow, vec3(0.06, 0.80, 0.40), smoothstep(0.23, 0.46, spectral));
            bow = mix(bow, vec3(0.98, 0.86, 0.12), smoothstep(0.46, 0.68, spectral));
            bow = mix(bow, vec3(1.0, 0.22, 0.07), smoothstep(0.68, 0.94, spectral));
            float clearSky = 1.0 - overcast * 0.72;
            sky += bow * edge * smoothstep(0.0, 0.10, ray.y) *
                   rainbowMoisture * clearSky * day * 0.62;
        }
    }
#endif
    sky += lightningBoltPosition.w*vec3(0.24,0.30,0.43)*(0.45+0.55*weatherStormAmount());
    return max(sky,vec3(0.0));
#endif
}
#endif
