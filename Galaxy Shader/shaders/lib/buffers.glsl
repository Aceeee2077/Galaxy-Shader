// All geometry and post-process colors remain linear HDR until composite4.
// Iris reads format directives inside this block; GLSL must not compile them.
/*
const int colortex0Format = RGBA16F;
const int colortex1Format = RGBA16F;
const int colortex2Format = RGBA16F;
const int colortex3Format = RGBA8;
const int colortex4Format = RGBA16F;
const int colortex5Format = R11F_G11F_B10F;
const int colortex6Format = R11F_G11F_B10F;
*/
// Iris parses these on the CPU and requires four explicit components.
const vec4 colortex0ClearColor = vec4(0.0,0.0,0.0,0.0);
const vec4 colortex1ClearColor = vec4(0.5,0.5,1.0,1.0);
const vec4 colortex2ClearColor = vec4(0.0,0.0,0.0,0.0);
const vec4 colortex3ClearColor = vec4(0.0,0.0,0.0,0.0);
const bool colortex4Clear = true;
const bool colortex5Clear = true;
const bool colortex6Clear = true;
