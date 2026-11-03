#ifndef SE_SETTINGS
#define SE_SETTINGS
// Galaxy Shader 1.15.32. Defaults correspond to HIGH.
const int shadowMapResolution = 2048; // [1024 2048 4096 8192]
const float shadowDistance = 128.0; // [64.0 96.0 128.0 192.0 256.0]
const float shadowIntervalSize = 2.0;
const float sunPathRotation = -25.0;
const float ambientOcclusionLevel = 0.65;
const float eyeBrightnessHalflife = 4.0;
const float centerDepthHalflife = 0.6;
const float wetnessHalflife = 12.0;
const float drynessHalflife = 70.0;
#define SHADOW_QUALITY 3 // [1 2 3 4 5]
#define SHADOW_SOFTNESS 1.25 // [0.5 0.75 1.0 1.25 1.5 2.0]
// Angular radius in degrees, shared by the visible disk and PCSS penumbra.
#define SUN_ANGULAR_RADIUS 2.0 // [0.5 1.0 1.5 2.0 2.5 3.0]
#define SKYLIGHT_STRENGTH 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define CLOUD_QUALITY 3 // [0 1 2 3 4]
#define CLOUD_COVERAGE 0.45 // [0.25 0.35 0.45 0.55 0.65]
#define CLOUD_SHADOW_STRENGTH 0.8 // [0.0 0.2 0.4 0.6 0.8 1.0]
#define CLOUD_SPEED 1.0 // [0.5 1.0 1.5 2.0]
#define CLOUD_TYPES 1 // [0 1]
#define NOCTILUCENT_CLOUDS 1 // [0 1]
// Two crossing gravity-wave trains inside the noctilucent sheet.
#define NLC_WAVES 1 // [0 1]
// Pastel diffraction fringes in thin cloud near the sun.
#define CLOUD_IRIDESCENCE 1 // [0 1]
// Broad volcanic-dust halo around the sun, warm inside and blue outside.
#define BISHOPS_RING 1 // [0 1]
// Iridescent winter polar-stratospheric lenticular sheets.
#define NACREOUS_CLOUDS 1 // [0 1]
#define WATER_QUALITY 2 // [0 1 2 3]
#define WATER_WAVES 1.0 // [0.0 0.5 1.0 1.5]
#define WATER_REFLECTIONS 0 // [0 1]
#define WATER_CLARITY 1.0 // [0.5 0.75 1.0 1.5 2.0]
// Low absorption preserves underwater terrain detail in shallow and medium water.
const float WATER_REFRACT_IOR = 1.333;
const vec3 WATER_ABSORPTION = vec3(0.180, 0.065, 0.028);
const vec3 WATER_ABSORPTION_UNDERWATER = vec3(0.055, 0.029, 0.018);
#define SSR_QUALITY 2 // [0 1 2 3 4]
#define AO_QUALITY 2 // [0 1 2 3 4]
#define INDIRECT_QUALITY 1 // [0 1 2]
#define COLORED_LIGHT_QUALITY 2 // [0 1 2 3]
#define COSMIC_SKY_QUALITY 2 // [0 1 2 3]
#define COSMIC_SKY_STRENGTH 0.25 // [0.0 0.25 0.5 0.75 1.0]
// Large hanging pleats that fold and gather the auroral curtain.
#define AURORA_FOLDS 1 // [0 1]
// Anti-solar Earth shadow / Belt of Venus, zodiacal light and night airglow.
#define TWILIGHT_OPTICS 1.0 // [0.0 0.5 1.0 1.5 2.0]
// Faint night-time ecliptic band and anti-solar gegenschein.
#define ZODIACAL_BAND 1 // [0 1]
// Brief green rim on the top of the solar disk at sunset or sunrise.
#define GREEN_FLASH 1 // [0 1]
// Differential refraction lifts and flattens a low sun or moon.
#define ATMOSPHERIC_REFRACTION 1 // [0 1]
// Faint cloud-shadow spokes converging on the anti-solar point at low sun.
#define ANTISOLAR_RAYS 1 // [0 1]
// 22-degree ice-crystal halo, sun dogs, tangent arc and sun pillar.
#define ICE_HALOS 1 // [0 1]
// Faint 46-degree ice ring, with the bright circumhorizontal arc at high sun.
#define ICE_HALO_COMPANIONS 1 // [0 1]
// Pastel diffraction rings in thin cloud around a bright moon.
#define LUNAR_CORONA 1 // [0 1]
// Fast atmospheric twinkling of stars, strongest near the horizon.
#define STAR_SCINTILLATION 1.0 // [0.0 0.5 1.0 1.5 2.0]
// Individual blue-white to warm-orange star tints and brightness spread.
#define STAR_COLOR 1 // [0 1]
// Faint horizontal gravity-wave banding in the night airglow layer.
#define AIRGLOW_RIPPLES 1 // [0 1]
#define CELESTIAL_EVENTS 1 // [0 1 2]
#define VOLUMETRIC_QUALITY 2 // [0 1 2 3 4]
#define WEATHER_QUALITY 3 // [0 1 2 3 4]
#define TERRAIN_FOG_QUALITY 2 // [0 1 2 3]
#define WEATHER_EFFECTS 1 // [0 1]
// Faint silver anti-lunar arc during rain with a bright moon.
#define MOONBOW 1 // [0 1]
// Broad white 42-degree bow in fog after rain.
#define FOGBOW 1 // [0 1]
#define RAIN_INTENSITY 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define RIPPLE_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define GODRAY_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define BLOOM_QUALITY 2 // [0 1 2 3]
#define BLOOM_STRENGTH 1.0 // [0.0 0.5 1.0 1.5 2.0]
#define EXPOSURE 1.25 // [0.5 0.75 1.0 1.25 1.5]
#define AUTO_EXPOSURE 0 // [0 1]
#define SATURATION 1.1 // [0.8 0.9 1.0 1.1 1.2]
#define CONTRAST 1.0 // [0.9 1.0 1.1]
#define FOG_DENSITY 1.0 // [0.5 0.75 1.0 1.25 1.5]
// Scales the dawn/dusk haze band and its volume light. 0 gives a crisp clear
// sunrise, 1 keeps a light morning mist and 2 restores a heavy fog bank.
#define DAWN_HAZE 1.0 // [0.0 0.5 1.0 1.5 2.0]
#define DOF_QUALITY 0 // [0 1 2 3]
#define MOTION_BLUR 0 // [0 1 2 3]
#define AA_QUALITY 1 // [0 1]
#define TAA_QUALITY 3 // [0 1 2 3]
#define TONEMAP_MODE 2 // [0 1 2]
#define PBR_MODE 1 // [0 1 2]
#define WIND_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define WET_SURFACES 1 // [0 1]
#define SUN_INTENSITY 1.0 // [0.5 0.75 1.0 1.25 1.5 2.0]
#define NIGHT_BRIGHTNESS 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define END_PLANETS 1 // [0 1]
#define END_ORBIT_SPEED 1.0 // [0.0 0.5 1.0 2.0]
#define SEASON_MODE 0 // [0 1 2 3 4]
#define SEASON_STRENGTH 1.0 // [0.0 0.5 1.0]
#define BIOME_BLEND 1 // [0 1]
#define PARTICLE_LAYER 1 // [0 1 2]
#define SURFACE_SEASONS 1 // [0 1]
#endif
