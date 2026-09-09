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
    star*=step(0.958,seed)*radius*radius/max(radius*radius,aa*aa);
    return mix(vec3(0.55,0.72,1.0),vec3(1.0,0.79,0.51),hash12(cell+9.2))*star*1.8;
}
float endOrbitSpeed(int index) {
    return index==0 ? 5.0 : (index==1 ? 3.0 : (index==2 ? 2.0 : 1.0));
}
float endOrbitDistance(int index) {
    return index==0 ? 13.0 : (index==1 ? 22.0 : (index==2 ? 34.0 : 48.0));
}
vec3 endPlanetCenter(int index, float phase) {
    float radius=endOrbitDistance(index);
    float start=index==0 ? -2.15 : (index==1 ? -1.15 : (index==2 ? -1.8 : -0.62));
    float angle=start+phase*endOrbitSpeed(index);
    // Inner orbits sit slightly higher; outer orbits stay nearer the star plane.
    float tilt=index==0 ? 0.16 : (index==1 ? 0.11 : (index==2 ? 0.08 : 0.05));
    return vec3(radius*cos(angle),12.0+radius*sin(angle)*sin(tilt),radius*sin(angle)*cos(tilt));
}
float endPlanetRadius(int index) {
    // Small inner world, mid molten world, large ringed giant, distant small giant.
    return index==0 ? 1.0 : (index==1 ? 2.7 : (index==2 ? 5.0 : 2.2));
}
// Closest positive intersection. Analytic intersections keep empty sky inexpensive.
float endSphere(vec3 ray, vec3 center, float radius) {
    float along=dot(ray,center);
    float perpendicular2=dot(center,center)-along*along;
    if(along<=0.0 || perpendicular2>=radius*radius) return 1e5;
    return along-sqrt(max(radius*radius-perpendicular2,0.0));
}
vec3 endPlanetSurface(vec3 n, int index, float phase) {
    float spin=phase*(float(index)+2.0);
    vec3 p=vec3(cos(spin)*n.x+sin(spin)*n.z,n.y,-sin(spin)*n.x+cos(spin)*n.z);
    float terrain=endNoise(p*5.0)*0.7+endNoise(p*13.0)*0.3;
    if(index==0) {
        float land=smoothstep(0.48,0.54,terrain);
        vec3 surface=mix(vec3(0.018,0.10,0.32),vec3(0.12,0.28,0.09),land);
        surface=mix(surface,vec3(0.72,0.87,0.93),smoothstep(0.78,0.94,abs(p.y)));
        float cloud=smoothstep(0.54,0.65,endNoise(p*9.0+vec3(4.0,0.0,0.0)));
        return mix(surface,vec3(0.85,0.90,0.95),cloud*0.85);
    }
    if(index==1) {
        vec3 rock=mix(vec3(0.18,0.038,0.015),vec3(0.64,0.25,0.085),terrain);
        return rock*(0.7+0.3*smoothstep(0.30,0.49,endNoise(p*22.0)));
    }
    if(index==2) {
        float bands=0.5+0.5*sin(p.y*36.0+endNoise(p*8.0)*6.0);
        return mix(vec3(0.26,0.12,0.048),vec3(0.82,0.64,0.36),bands)*(0.8+terrain*0.4);
    }
    float cracks=smoothstep(0.0,0.06,abs(terrain-0.50));
    return mix(vec3(0.055,0.25,0.36),vec3(0.48,0.78,0.88),cracks)*(0.7+terrain*0.5);
}
vec3 endPlanetGlowTint(int index) {
    // Thin cold atmosphere, volcanic haze, dusty amber gas giant, icy cyan shell.
    return index==0 ? vec3(0.45,0.72,1.15)
        : (index==1 ? vec3(1.05,0.48,0.14)
        : (index==2 ? vec3(1.00,0.70,0.30) : vec3(0.35,0.82,1.05)));
}
float endPlanetGlowStrength(int index) {
    return index==0 ? 0.75 : (index==1 ? 1.05 : (index==2 ? 0.95 : 0.80));
}
// Soft exosphere scattering around a planet's silhouette. rho==1 is the limb:
// the glow peaks there, keeps a narrow rim over the outer part of the disk,
// and falls off in a wide haze outside. The lit side (facing the central star)
// scatters more, which reads as light spilling around the planet through dust.
vec3 endPlanetGlow(vec3 ray, vec3 center, float radius, vec3 star, int index) {
    vec3 offset=center-ray*dot(ray,center);
    float rho=length(offset)/radius;
    if(rho>4.5) return vec3(0.0);
    float d=rho-1.0;
    float rim=exp(-d*d*18.0);
    float inside=rho<1.0 ? smoothstep(0.78,1.0,rho) : 1.0;
    float haze=exp(-max(d,0.0)*1.55)*inside;
    vec3 closest=ray*dot(ray,center);
    vec3 outward=(closest-center)/max(length(offset),1e-5);
    vec3 toStar=normalize(star-closest);
    float lit=0.40+0.60*pow(max(dot(outward,toStar),0.0),1.25);
    return endPlanetGlowTint(index)*lit*endPlanetGlowStrength(index)*(0.42*rim+0.20*haze);
}
vec3 endCosmos(vec3 ray, bool disks) {
    float nebula=pow(fbm(ray.xz/max(abs(ray.y)+0.4,0.4)*3.0,4),3.0);
    vec3 sky=vec3(0.005,0.004,0.012)+vec3(0.045,0.024,0.07)*nebula;
#if END_PLANETS == 1
    float footprint=max(length(dFdx(ray)),length(dFdy(ray)));
    // Broad-band nebula, fixed stars: no per-frame random sparkle.
    float belt=pow(max(0.0,1.0-abs(dot(ray,normalize(vec3(0.3,1.0,0.4))))),7.0);
    sky+=vec3(0.025,0.019,0.060)*belt*(0.3+endNoise(ray*18.0));
    if(!disks) return sky;
    sky+=endStars(ray,footprint);
    // Iris resets frameTimeCounter at 3600 s. Every supported speed completes
    // an integer number of revolutions at that boundary, including axial spin.
    float phase=2.0*PI*fract(frameTimeCounter*(END_ORBIT_SPEED/900.0));
    vec3 starCenter=vec3(0.0,12.0,0.0);
    float starDot=max(dot(ray,normalize(starCenter)),0.0);
    sky+=vec3(0.20,0.10,0.035)*pow(starDot,60.0);
    float nearest=endSphere(ray,starCenter,0.8);
    if(nearest<1e4) sky=vec3(3.8,2.8,1.4);
    for(int i=0;i<4;++i) {
        vec3 center=endPlanetCenter(i,phase);
        float radius=endPlanetRadius(i);
        float hit=endSphere(ray,center,radius);
        if(hit<nearest) {
            vec3 n=normalize(ray*hit-center);
            vec3 light=normalize(starCenter-(ray*hit));
            float lit=max(dot(n,light),0.0);
            vec3 surface=endPlanetSurface(n,i,phase);
            vec3 tint=i==0 ? vec3(0.09,0.35,0.95) : (i==1 ? vec3(0.7,0.20,0.07) : vec3(0.18,0.48,0.70));
            float rim=pow(1.0-max(dot(n,-ray),0.0),3.0);
            vec3 planet=surface*(0.085+lit*1.65)+tint*rim*(0.06+lit*0.28);
            float edge=radius-length(ray*dot(ray,center)-center);
            float coverage=smoothstep(0.0,max(footprint*hit,0.0001),edge);
            sky=mix(sky,planet,coverage);
            nearest=hit;
        }
    }
    // Second pass adds the atmosphere glow over the sky after disk coverage, so
    // halos stay visible around every silhouette while rings can still draw on
    // top of the giant's own glow below.
    for(int i=0;i<4;++i) {
        vec3 center=endPlanetCenter(i,phase);
        sky+=endPlanetGlow(ray,center,endPlanetRadius(i),starCenter,i);
    }
    // Intersect the giant's tilted ring plane, then depth-test against all spheres.
    vec3 center=endPlanetCenter(2,phase);
    vec3 ringNormal=normalize(vec3(0.20,1.0,0.32));
    float denom=dot(ray,ringNormal);
    if(abs(denom)>0.001) {
        float hit=dot(center,ringNormal)/denom;
        if(hit>0.0 && hit<nearest) {
            vec3 local=ray*hit-center;
            float r=length(local);
            float aa=max(footprint*hit,0.02);
            float giantRadius=endPlanetRadius(2);
            float ringInner=giantRadius*1.25;
            float ringOuter=giantRadius*2.0;
            float ringGap=giantRadius*1.68;
            float mask=smoothstep(ringInner-aa,ringInner+aa,r)*(1.0-smoothstep(ringOuter-aa,ringOuter+aa,r));
            float gap=smoothstep(0.08,0.15,abs(r-ringGap));
            float bands=0.70+0.16*sin(r*28.0)+0.08*sin(r*71.0);
            // The planet casts a shadow onto its own rings.
            vec3 light=normalize(starCenter-(ray*hit));
            float shade=endSphere(light,-local,giantRadius)<1e4 ? 0.22 : 1.0;
            sky=mix(sky,vec3(0.55,0.39,0.20)*bands*shade,mask*gap*0.85);
        }
    }
#endif
    return sky;
}
#endif
#endif
