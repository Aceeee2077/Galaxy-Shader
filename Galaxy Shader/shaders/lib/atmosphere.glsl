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
    // Relative optical path: warm light at grazing incidence, near-neutral
    // daylight overhead. Separate chroma from the existing luminance budget,
    // avoiding another scalar attenuation of the low sun or its water glints.
    float extraPath=max(inversesqrt(h*h+0.0025)-1.0,0.0);
    vec3 tint=vec3(1.0,0.985,0.965)*exp(-vec3(0.0,0.045,0.135)*extraPath);
    float energy=mix(0.66,0.97,smoothstep(0.0,0.45,h));
    return tint*(energy/max(luminance(tint),1e-4));
}
// A low-order diffuse sky probe, shared by surfaces, clouds and water. Its
// hemispheres follow sun elevation and weather without another sky ray march.
vec3 skyIrradiance(vec3 n) {
    float day=dayAmount();
    float lowSun=dawnDuskAmount();
    float overcast=weatherOvercastAmount();
    float skyHemisphere=sat(n.y*0.5+0.5);
    vec3 zenith=mix(vec3(0.012,0.018,0.030)*NIGHT_BRIGHTNESS,
                    vec3(0.22,0.29,0.40),day);
    vec3 horizon=mix(vec3(0.018,0.023,0.034)*NIGHT_BRIGHTNESS,
                     mix(vec3(0.28,0.30,0.33),vec3(0.25,0.275,0.33),lowSun*0.65),day);
    vec3 cloudy=mix(vec3(0.015,0.019,0.027)*NIGHT_BRIGHTNESS,
                    vec3(0.22,0.24,0.27),day);
    zenith=mix(zenith,cloudy,overcast*0.85);
    horizon=mix(horizon,cloudy,overcast*0.85);
    float sunward=0.5+0.5*dot(n.xz,sunDirection().xz);
    vec3 upper=zenith*skyHemisphere+horizon*(1.0-abs(n.y))*0.24;
    upper+=sunlightColor()*lowSun*day*sunward*(1.0-overcast)*0.025;
    // Muted ground bounce gives undersides shape without lifting closed caves.
    vec3 ground=mix(vec3(0.003,0.004,0.006)*NIGHT_BRIGHTNESS,
                    vec3(0.055,0.047,0.035),day)*(1.0-skyHemisphere);
    // Low sun illuminates a small part of the dome. Reducing diffuse fill here
    // preserves bright sun-facing surfaces against cool, readable tree shade.
    float twilightFill=1.0-0.42*lowSun*day*(1.0-overcast);
    return (upper+ground)*twilightFill*(1.0-weatherStormAmount()*0.42)*
           (1.0-0.65*eclipseAmount())*SKYLIGHT_STRENGTH;
}
vec3 directionalRadiance() {
    float d = dayAmount();
    float sunHeight=sunDirection().y;
    // The old air-mass term and shared horizon fade suppressed low-angle sun
    // twice. Keep strong direct light once the solar disk clears the horizon;
    // the surface cosine still provides the natural grazing-angle falloff.
    float sunVisibility=smoothstep(-0.04,0.045,sunHeight);
    float lowSunGain=mix(1.12,1.0,smoothstep(0.10,0.60,sunHeight));
    vec3 sun = sunlightColor() * (3.35*SUN_INTENSITY*lowSunGain*sunVisibility) * seasonSunTint();
    float phase = 0.45 + 0.55 * abs(float(moonPhase)-4.0)/4.0;
    vec3 moon = vec3(0.12,0.15,0.20)*NIGHT_BRIGHTNESS*phase*seasonSkyTint();
    moon*=smoothstep(0.0,0.12,abs(sunHeight));
    return mix(moon,sun,d)*(1.0-0.55*weatherOvercastAmount())*(1.0-0.64*weatherRainAmount())*
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
    // A pale horizon graduates into a blue zenith instead of a uniformly
    // saturated dome. Keep this broad component neutral even at low sun.
    scatter+=vec3(0.095,0.115,0.135)*pow(1.0-h,5.0)*smoothstep(-0.08,0.18,sun.y);
    scatter += sunlightColor()*mie*0.012*smoothstep(-0.12,0.1,sun.y);
    float sunset = (1.0-smoothstep(0.03,0.35,abs(sun.y)))*smoothstep(-0.15,0.0,sun.y);
    // Keep the warm band close to the horizon and on the sun's side. The old
    // isotropic share tinted most of the dome, so a low morning sun washed the
    // whole sky into the same flat grey as overcast weather.
    scatter += vec3(0.72,0.34,0.10)*sunset*pow(1.0-h,5.5)*(0.06+0.94*pow(max(mu,0.0),6.0));
    float golden=goldenHourAmount()*(1.0-weatherOvercastAmount());
    float goldenAir=golden*pow(1.0-h,2.5)*(0.08+0.92*pow(max(mu,0.0),4.0));
    scatter*=mix(vec3(1.0),vec3(0.98,0.91,0.68),goldenAir);
    scatter+=vec3(0.48,0.22,0.065)*golden*pow(1.0-h,2.5)*
             (0.06+0.94*pow(max(mu,0.0),4.0));
    vec3 night = mix(vec3(0.006,0.009,0.018),vec3(0.018,0.023,0.037),pow(1.0-h,3.0))*NIGHT_BRIGHTNESS;
    vec3 sky = mix(night,scatter,day);
    // A blue twilight dome survives after direct sunlight fades. Local pink
    // horizon light replaces the previous broad yellow overlay.
    float blueHour=exp(-pow((sun.y+0.075)/0.065,2.0));
    sky+=vec3(0.012,0.025,0.065)*blueHour*(0.35+0.65*h);
    sky+=vec3(0.065,0.022,0.032)*blueHour*pow(1.0-h,6.0)*
         (0.2+0.8*pow(max(mu,0.0),2.0));
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
    // A compact solar aureole stays near the disk. Unlike a screen-wide warm
    // haze, it leaves the blue sky and foreground contrast intact. Lower cloud
    // layers composite over this light, so their opaque cores occlude it.
    float solarAngle=max(1.0-mu,0.0);
    float radius=SUN_ANGULAR_RADIUS*(PI/180.0);
    float diskEdge=1.0-cos(radius);
    float haloDistance=max(solarAngle-diskEdge,0.0);
    float solarHalo=exp(-haloDistance*500.0)*0.10+exp(-haloDistance*1800.0)*1.80;
    sky+=sunlightColor()*solarHalo*day*smoothstep(-0.04,0.045,sun.y)*
         (1.0-overcast)*(1.0-0.95*eclipse)*SUN_INTENSITY;
    if (disks && ray.y>-0.02) {
        // Keep the disk edge stable with resolution; the angular radius also
        // controls contact-hardening shadows, rather than an unrelated size.
        float diskWidth=max(fwidth(mu),diskEdge*0.06);
        float solarDisk=smoothstep(cos(radius)-diskWidth,cos(radius)+diskWidth,mu);
        sky += sunlightColor()*18.0*solarDisk*day*(1.0-overcast)*(1.0-0.95*eclipse)*SUN_INTENSITY;
        sky += vec3(1.00,0.82,0.55)*exp(-pow((1.0-mu)*58.0,2.0))*eclipse*2.2;
        vec3 moon = worldDirection(moonPosition);
        sky += vec3(1.2,1.3,1.5)*smoothstep(0.99976,0.99994,dot(ray,moon))*(1.0-day)*(1.0-overcast);
        vec2 starUV = vec2(atan(ray.z,ray.x),asin(clamp(ray.y,-1.0,1.0)))*vec2(700.0,900.0);
        float star = step(0.996,hash12(floor(starUV)))*pow(max(1.0-length(fract(starUV)-0.5)*2.0,0.0),4.0);
        sky += vec3(star*0.7*(1.0-day)*(1.0-overcast)*smoothstep(0.0,0.2,ray.y));
#if COSMIC_SKY_QUALITY > 0
        float cosmicNight = (1.0-day)*(1.0-overcast*0.82);
        sky += galaxyNebula(ray)*cosmicNight*(0.55+0.45*float(COSMIC_SKY_QUALITY>=2))*COSMIC_SKY_STRENGTH;
#if COSMIC_SKY_QUALITY >= 2
        sky += auroraSky(ray,cosmicNight*biomeAuroraBoost()*(1.0+auroraStormAmount()*0.9))*COSMIC_SKY_STRENGTH;
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
