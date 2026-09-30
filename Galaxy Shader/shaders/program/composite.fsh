#include "/lib/common.glsl"
#include "/lib/clouds.glsl"
#include "/lib/fog.glsl"
#include "/lib/volumetrics.glsl"
#include "/lib/caustics.glsl"
#include "/lib/biome.glsl"
#include "/lib/seasons.glsl"
#include "/lib/particles.glsl"
uniform sampler2D colortex0, colortex3, depthtex0;
varying vec2 texcoord;
/* DRAWBUFFERS:0 */
void main() {
    float d=texture2D(depthtex0,texcoord).r;
    bool sky=skyDepth(d)>0.5;
    vec3 player=playerPosition(viewPosition(texcoord,d));
    if(sky) player=safeNormalize(player)*far;
    vec3 color=texture2D(colortex0,texcoord).rgb;
    float hand=texture2D(colortex3,texcoord).b;
    if(hand<0.5) {
#if DIMENSION == 0 && SURFACE_SEASONS == 1
        float heat=biomeDesert()*dayAmount()*max(seasonWeights().y,0.5)*(1.0-weatherRainAmount());
        if(heat>0.02 && !sky) {
            vec2 warp=vec2(sin(player.z*0.35+frameTimeCounter*2.0),cos(player.x*0.30+frameTimeCounter*1.7))*
                      pixelSize()*heat*3.0;
            color=texture2D(colortex0,clamp(texcoord+warp,pixelSize(),1.0-pixelSize())).rgb;
        }
#endif
#if DIMENSION == 0
        if(isEyeInWater==1 && !sky) {
#if WATER_QUALITY > 2
            // Only the highest water profile pays for the distance blur; the
            // absorption fog already carries the depth cue at lower profiles.
            float uz=length(viewPosition(texcoord,d));
            vec2 ublur=pixelSize()*(0.45+uz*0.018);
            vec3 ucolor=color;
            float uweight=1.0;
            int utaps=4;
            for(int i=1;i<4;++i) {
                vec2 suv=clamp(texcoord+diskSample(i,utaps)*ublur,pixelSize(),1.0-pixelSize());
                float sd=texture2D(depthtex0,suv).r;
                if(texture2D(colortex3,suv).b>0.5) continue;
                float sz=length(viewPosition(suv,sd));
                float w=1.0-smoothstep(0.0,max(uz*1.5,1.0),abs(sz-uz));
                ucolor+=texture2D(colortex0,suv).rgb*w;
                uweight+=w;
            }
            color=ucolor/uweight;
#endif
            // Animated caustic veins on underwater terrain.
            vec3 world=cameraPosition+player;
            vec2 causticPos=world.xz*0.35+vec2(frameTimeCounter*0.030,frameTimeCounter*0.021);
            float caustics=causticField(causticPos);
#if WATER_QUALITY > 1
            caustics=caustics*0.70+causticField(causticPos*0.5+vec2(5.0,3.0))*0.50;
#else
            caustics*=1.20;
#endif
            color+=vec3(0.08,0.20,0.22)*caustics*exp(-length(player)*0.025)*0.55;
        }
#endif
        // The procedural sky already includes its atmospheric path.
        vec3 particleRay=safeNormalize(player);
        float airDistance=sky ? 26.0 : min(length(player),40.0);
        vec3 airWorld=cameraPosition+particleRay*airDistance;
        float particleVisibility=1.0;
#if DIMENSION == 1
        // Keep End cosmic motes in the sky so the planet layer never alters
        // opaque terrain pixels.
        particleVisibility=sky ? 1.0 : 0.0;
#endif
        color+=particleLayer(airWorld,airDistance)*particleVisibility;
        if(!sky || isEyeInWater!=0) color=applyFog(color,player,sky);
        color+=volumetricLight(player);
#if DIMENSION == 0
        float caveFactor=(1.0-smoothstep(0.02,0.30,float(eyeBrightnessSmooth.y)/240.0))*float(isEyeInWater==0);
        if(caveFactor>0.0 && !sky) {
            vec3 world=cameraPosition+player;
            float motes=pow(skyNoise3(world*0.55+vec3(0.0,frameTimeCounter*0.05,0.0)),4.0);
            color+=vec3(0.004,0.012,0.010)*motes*caveFactor*0.25;
        }
#endif
    }
    gl_FragData[0]=vec4(max(color,vec3(0.0)),1.0);
}
