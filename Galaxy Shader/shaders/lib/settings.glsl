#ifndef SE_SETTINGS
#define SE_SETTINGS
// Galaxy Shader 1.5.0. Defaults correspond to HIGH.
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
#define CLOUD_QUALITY 3 // [0 1 2 3 4]
#define CLOUD_COVERAGE 0.45 // [0.25 0.35 0.45 0.55 0.65]
#define CLOUD_SPEED 1.0 // [0.5 1.0 1.5 2.0]
#define WATER_QUALITY 2 // [0 1 2 3]
#define WATER_WAVES 1.0 // [0.0 0.5 1.0 1.5]
#define SSR_QUALITY 2 // [0 1 2 3 4]
#define AO_QUALITY 2 // [0 1 2 3 4]
#define INDIRECT_QUALITY 1 // [0 1 2]
#define VOLUMETRIC_QUALITY 2 // [0 1 2 3 4]
#define WEATHER_QUALITY 3 // [0 1 2 3 4]
#define TERRAIN_FOG_QUALITY 2 // [0 1 2 3]
#define RAIN_INTENSITY 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define RIPPLE_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define GODRAY_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define BLOOM_QUALITY 2 // [0 1 2 3]
#define EXPOSURE 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define AUTO_EXPOSURE 1 // [0 1]
#define SATURATION 1.0 // [0.8 0.9 1.0 1.1 1.2]
#define CONTRAST 1.0 // [0.9 1.0 1.1]
#define FOG_DENSITY 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define DOF_QUALITY 0 // [0 1 2 3]
#define MOTION_BLUR 0 // [0 1 2 3]
#define AA_QUALITY 1 // [0 1]
#define TAA_QUALITY 3 // [0 1 2 3]
#define TONEMAP_MODE 2 // [0 1 2]
#define PBR_MODE 1 // [0 1 2]
#define WIND_STRENGTH 1.0 // [0.0 0.5 1.0 1.5]
#define WET_SURFACES 1 // [0 1]
#define SUN_INTENSITY 1.0 // [0.75 1.0 1.25]
#define NIGHT_BRIGHTNESS 1.0 // [0.5 0.75 1.0 1.25 1.5]
#define END_PLANETS 1 // [0 1]
#define END_ORBIT_SPEED 1.0 // [0.0 0.5 1.0 2.0]
#endif
