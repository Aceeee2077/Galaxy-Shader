#include "/lib/common.glsl"
#include "/lib/weather.glsl"
uniform sampler2D texture;
varying vec2 vTex, vLight;
varying vec4 vColor;
varying vec3 vPlayer, vNormal, vTangent, vBitangent;
varying float vId;
/* DRAWBUFFERS:0 */
void main() {
    vec4 source = texture2D(texture, vTex) * vColor;
#if DIMENSION != 0 || WEATHER_QUALITY == 0
    if (source.a < 0.01) discard;
    gl_FragData[0] = vec4(toLinear(source.rgb), source.a);
#else
    float rain = weatherRainAmount();
    if (rain < 0.002) discard;
    float distanceToEye = length(vPlayer);
    vec2 wind = weatherWindDirection();
    float storm = weatherStormAmount();
    float nearFactor = 1.0 - smoothstep(10.0, 82.0, distanceToEye);
    float farDensity = smoothstep(18.0, 110.0, distanceToEye);

    // Warp the supplied streak silhouette to follow the procedural wind. The
    // atlas remains a strict coverage mask: drawing outside it causes dozens of
    // precipitation cards to accumulate into the opaque white curtain seen in
    // game. Shape breakup, motion, density and color are still authored here.
    vec2 rainUV = vTex;
    float shear = (0.075 + WIND_STRENGTH * 0.045 + storm * 0.045) *
                  mix(1.0,0.68,farDensity);
    rainUV.x += (vTex.y - 0.5) * wind.x * shear;
    rainUV = clamp(rainUV, vec2(0.002), vec2(0.998));
    source = texture2D(texture, rainUV) * vColor;
    float atlasMask = pow(smoothstep(0.025, 0.82, source.a), 1.35);

    vec2 worldCell = floor((vPlayer.xz + cameraPosition.xz) * 0.55);
    float cardNoise = hash12(worldCell);
    float densityGate = smoothstep(mix(0.20, 0.43, farDensity), 0.92, cardNoise);

    // Cut the atlas' continuous vertical streak into independently phased,
    // tapered segments. This changes the silhouette itself rather than merely
    // scrolling the original line faster.
    float lengthNoise = hash12(worldCell + vec2(7.3,19.1));
    float dashCount = mix(3.2,6.4,farDensity) + lengthNoise * 1.4;
    float fallSpeed = 2.4 + storm * 1.7 + lengthNoise * 0.9;
    float dashPhase = fract(vTex.y * dashCount - frameTimeCounter * fallSpeed +
                            cardNoise * 9.7);
    float dashLength = mix(0.30,0.62,lengthNoise) * mix(1.0,0.72,farDensity);
    float dashHead = smoothstep(0.0,0.055,dashPhase);
    float dashTail = 1.0-smoothstep(max(dashLength-0.16,0.08),dashLength,dashPhase);
    float dashMask = dashHead * dashTail;
    float longitudinalTaper = pow(sat(1.0-dashPhase/max(dashLength,0.08)),0.32);
    float breakupNoise = 0.0;
    float breakupWeight = 0.0;
    for (int i = 0; i < WEATHER_QUALITY; ++i) {
        float fi = float(i);
        float weight = 1.0 / (1.0 + fi);
        vec2 dashPosition = vec2(vTex.y * (7.0 + fi * 4.0) - frameTimeCounter *
                                 (12.0 + storm * 7.0 + fi * 2.5),
                                 cardNoise * 31.0 + fi * 9.3);
        breakupNoise += valueNoise(dashPosition) * weight;
        breakupWeight += weight;
    }
    float breakup = mix(0.62, 1.0, smoothstep(0.12, 0.88,
                         breakupNoise / max(breakupWeight, 1.0)));
    float distanceAlpha = mix(0.34, 0.105, farDensity) * mix(0.82, 1.0, nearFactor);
    float alpha = atlasMask * densityGate * dashMask *
                  mix(0.58,1.0,longitudinalTaper) * breakup * distanceAlpha * rain;
    if (alpha < 0.006) discard;

    vec3 rainColor = mix(toLinear(vec3(0.30, 0.37, 0.46)),
                         toLinear(vec3(0.52, 0.59, 0.67)), nearFactor);
    rainColor *= 0.82 + breakup * 0.24;
    rainColor += lightningBoltPosition.w * vec3(0.24, 0.32, 0.48) * (0.30 + storm);
    gl_FragData[0] = vec4(rainColor, min(alpha, 0.38));
#endif
}
