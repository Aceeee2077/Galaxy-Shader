#ifndef SE_END_SKY
#define SE_END_SKY
#include "/lib/noise.glsl"
#if DIMENSION == 1
// Direction-space scenery: independent of camera translation and terrain lighting.
float endNoise(vec3 p) {
    return (valueNoise(p.xy)+valueNoise(p.yz+17.3)+valueNoise(p.zx+31.7))/3.0;
}
vec3 endStars(vec3 ray, float footprint) {
    // Cube projection avoids the polar compression of longitude/latitude stars.
    vec3 a=abs(ray);
    vec2 uv; float face;
    if(a.x>=a.y && a.x>=a.z) { uv=ray.yz/a.x; face=sign(ray.x); }
    else if(a.y>=a.z) { uv=ray.xz/a.y; face=2.0*sign(ray.y); }
    else { uv=ray.xy/a.z; face=3.0*sign(ray.z); }
    vec2 grid=uv*150.0;
    vec2 cell=floor(grid);
    float seed=hash12(cell+face*73.1);
    vec2 center=vec2(hash12(cell+face*19.7),hash12(cell+face*41.3));
    center=0.22+center*0.56;
    float radius=mix(0.045,0.12,seed);
    float aa=clamp(footprint*150.0,0.02,0.6);
    float star=1.0-smoothstep(max(0.0,radius-aa),radius+aa,length(fract(grid)-center));
    star*=step(0.982,seed)*radius*radius/max(radius*radius,aa*aa);
    return mix(vec3(0.55,0.72,1.0),vec3(1.0,0.79,0.51),hash12(cell+9.2))*star*0.85;
}
// Only the reference-inspired ringed giant remains.
const float END_GIANT_RADIUS=13.0;
vec3 endGiantCenter(float phase) {
    return vec3(-26.0*cos(phase),15.0+2.0*sin(phase),-38.0-8.0*sin(phase));
}
// Closest positive intersection. Analytic intersections keep empty sky inexpensive.
float endSphere(vec3 ray, vec3 center, float radius) {
    float along=dot(ray,center);
    float perpendicular2=dot(center,center)-along*along;
    if(along<=0.0 || perpendicular2>=radius*radius) return 1e5;
    return along-sqrt(max(radius*radius-perpendicular2,0.0));
}
vec3 endGiantSurface(vec3 n, float spin) {
    vec3 p=vec3(cos(spin)*n.x+sin(spin)*n.z,n.y,-sin(spin)*n.x+cos(spin)*n.z);
    float terrain=endNoise(p*5.0)*0.7+endNoise(p*13.0)*0.3;
    float bands=0.5+0.5*sin(p.y*36.0+endNoise(p*8.0)*6.0);
    return mix(vec3(0.085,0.095,0.125),vec3(0.25,0.26,0.31),bands*0.35+0.25)*(0.8+terrain*0.4);
}
// Soft exosphere scattering around a planet's silhouette. rho==1 is the limb:
// the glow peaks there, keeps a narrow rim over the outer part of the disk,
// and falls off in a wide haze outside. The lit side (facing the central star)
// scatters more, which reads as light spilling around the planet through dust.
vec3 endGiantGlow(vec3 ray, vec3 center, float radius, vec3 star) {
    if(dot(ray,center)<=0.0) return vec3(0.0);
    vec3 offset=center-ray*dot(ray,center);
    float rho=length(offset)/radius;
    if(rho>6.0) return vec3(0.0);
    float d=rho-1.0;
    float limb=exp(-pow(d*65.0,2.0));
    float outside=exp(-max(d,0.0)*14.0);
    float inside=rho<1.0 ? exp(-max(-d,0.0)*45.0) : 1.0;
    vec3 closest=ray*dot(ray,center);
    vec3 outward=(closest-center)/max(length(offset),1e-5);
    vec3 toStar=normalize(star-closest);
    float lit=0.35+0.65*pow(max(dot(outward,toStar),0.0),1.05);
    return vec3(0.88,0.82,1.00)*lit*0.90*
           (0.32*limb+0.025*outside*inside);
}

// One belt of the shattered halo. Each angular sector owns a single shard whose
// radius, thickness and tint come from a hash, and some sectors stay empty, so
// the halo reads as chipped fragments instead of a continuous round ring.
vec3 endShardBelt(float angle, float rho, float sectors, float inner, float outer, float aa) {
    float sector=angle/(2.0*PI)*sectors;
    float index=floor(sector);
    float offset=fract(sector)-0.5;
    float seed=hash12(vec2(index,17.3));
    float seed2=hash12(vec2(index,53.1));
    float radius=mix(inner,outer,seed);
    float thickness=mix(0.045,0.105,seed2);
    float shard=exp(-pow((rho-radius)/(thickness+aa),2.0));
    shard*=1.0-smoothstep(mix(0.17,0.29,seed2),0.45+aa,abs(offset));
    shard*=step(0.24,hash12(vec2(index,91.7)));
    vec3 tint=mix(vec3(0.58,0.40,0.95),vec3(0.30,0.78,0.94),seed);
    return tint*(shard*2.35);
}

// Centre of the End sky: a faceted rift core. A bright crystal star with four
// long diffraction streaks, two counter-facing plasma jets and two broken belts
// of angular shards share one closed-form angular frame. The silhouette is
// spiked and segmented on purpose so it never reads as a round event horizon
// with a smooth dust disk, and nothing is marched or integrated per pixel.
// The giant uses this object as its light source.
vec3 endRift(vec3 ray, vec3 center, float footprint, float phase) {
    vec3 axis=normalize(center);
    float forward=dot(ray,axis);
    if(forward<=0.0) return vec3(0.0);
    vec3 right=normalize(cross(axis,vec3(0,1,0)));
    vec3 up=cross(right,axis);
    float scale=length(center)/4.8;
    vec2 q=vec2(dot(ray,right),dot(ray,up))/forward*scale;
    q=mat2(0.978,0.208,-0.208,0.978)*q;
    float rho=length(q);
    if(rho>3.0) return vec3(0.0);
    float aa=max(footprint*scale,0.010);
    float angle=atan(q.y,q.x);
    // A quarter turn per orbital cycle keeps every supported speed an integer
    // number of rotations at the 3600 s clock reset.
    float spin=phase*0.5*PI;
    float turn=angle+spin;

    // Faceted crystal core with a soft bloom and four long lens streaks.
    float facets=0.72+0.28*cos(angle*6.0-spin*0.7);
    vec3 color=vec3(0.84,0.88,1.00)*exp(-pow(rho/0.30,2.2))*(1.30*facets+0.55);
    float streaked=pow(abs(cos(turn)),24.0)*exp(-rho*0.90);
    float crossed=pow(abs(sin(turn)),16.0)*exp(-rho*1.30);
    color+=vec3(0.52,0.78,1.00)*(streaked*1.85+crossed*1.05);

    // Two counter-facing plasma jets along the rift axis.
    vec2 jet=vec2(-0.26,0.966);
    float along=dot(q,jet);
    float across=dot(q,vec2(-jet.y,jet.x));
    float beam=exp(-pow(across/(0.052+aa*0.6),2.0))*exp(-abs(along)*1.25)*
               smoothstep(0.12,0.50,abs(along))*(1.0-smoothstep(1.8,2.6,abs(along)));
    color+=vec3(0.36,0.80,1.00)*beam*1.55;

    // Two broken shard belts plus a faint violet nebula bloom behind the core.
    color+=endShardBelt(angle,rho,10.0,0.78,1.18,aa);
    color+=endShardBelt(angle,rho,7.0,1.45,2.15,aa);
    color+=vec3(0.30,0.20,0.55)*exp(-rho*0.90)*0.42;
    return color;
}

vec3 endCosmos(vec3 ray, bool disks) {
    float nebula=pow(fbm(ray.xz/max(abs(ray.y)+0.4,0.4)*3.0,4),3.0);
    vec3 sky=vec3(0.00045,0.00055,0.0008)+vec3(0.003,0.0034,0.0045)*nebula;
    float footprint=max(length(dFdx(ray)),length(dFdy(ray)));
    // The planet toggle leaves a static star field instead of a blank dome.
    if(disks) sky+=endStars(ray,footprint);
#if END_PLANETS == 1
    // Broad-band nebula, fixed stars: no per-frame random sparkle.
    float belt=pow(max(0.0,1.0-abs(dot(ray,normalize(vec3(0.3,1.0,0.4))))),7.0);
    sky+=vec3(0.0018,0.0020,0.0025)*belt*(0.3+endNoise(ray*18.0));
    if(!disks) return sky;
    // Iris resets frameTimeCounter at 3600 s. Every supported speed completes
    // an integer number of revolutions at that boundary, including axial spin.
    float phase=2.0*PI*fract(frameTimeCounter*(END_ORBIT_SPEED/900.0));
    vec3 starCenter=vec3(0.0,16.0,-42.0);
    // The rift core is a light source, not a solid body: no opaque disk is
    // depth-tested against the planets, so they stay free to pass in front.
    float nearest=1e5;
    sky+=endRift(ray,starCenter,footprint,phase);
    vec3 center=endGiantCenter(phase);
    float radius=END_GIANT_RADIUS;
    float planetHit=endSphere(ray,center,radius);
    if(planetHit<nearest) {
        vec3 n=normalize(ray*planetHit-center);
        vec3 light=normalize(starCenter-(ray*planetHit));
        float lit=max(dot(n,light),0.0);
        float spin=2.0*PI*fract(frameTimeCounter*END_ORBIT_SPEED*8.0/3600.0);
        vec3 surface=endGiantSurface(n,spin);
        float rim=pow(1.0-max(dot(n,-ray),0.0),3.0);
        vec3 planet=surface*vec3(0.92,0.93,1.02)*(0.09+lit*1.35)+
                    vec3(0.30,0.44,0.80)*rim*(0.05+lit*0.25);
        float edge=radius-length(ray*dot(ray,center)-center);
        float coverage=smoothstep(0.0,max(footprint*planetHit,0.0001),edge);
        sky=mix(sky,planet,coverage);
        nearest=planetHit;
    }
    if(dot(ray,center)-radius<=nearest)
        sky+=endGiantGlow(ray,center,radius,starCenter);
    // Depth-test the giant's ring against its body and the black hole.
    vec3 ringNormal=normalize(vec3(0.20,1.0,0.32));
    float denom=dot(ray,ringNormal);
    if(abs(denom)>0.001) {
        float hit=dot(center,ringNormal)/denom;
        if(hit>0.0 && hit<nearest) {
            vec3 local=ray*hit-center;
            float r=length(local);
            float aa=max(footprint*hit,0.02);
            float giantRadius=END_GIANT_RADIUS;
            float ringInner=giantRadius*1.22;
            float ringOuter=giantRadius*3.3;
            float mask=smoothstep(ringInner-aa,ringInner+aa,r)*(1.0-smoothstep(ringOuter-aa,ringOuter+aa,r));
            if(mask<=0.0) return sky;
            float gap=smoothstep(0.10,0.20,abs(r-giantRadius*1.72));
            float bands=0.66+0.16*sin(r*8.0)*exp(-aa*8.0)+
                        0.10*sin(r*23.0)*exp(-aa*23.0)+0.08*sin(r*61.0)*exp(-aa*61.0);
            float dust=0.45+0.55*endNoise(local*1.4);
            float clumps=smoothstep(0.45,0.82,endNoise(local*3.2));
            vec3 dustColor=mix(vec3(0.24,0.26,0.30),vec3(0.72,0.76,0.88),dust);
            vec3 light=normalize(starCenter-(ray*hit));
            float shade=endSphere(light,-local,giantRadius)<1e4 ? 0.28 : 1.0;
            sky=mix(sky,dustColor*bands*shade*(0.85+0.15*clumps),mask*gap*0.90);
        }
    }
#endif
    return sky;
}
#endif
#endif
