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
    // Inner planets sweep quickly; outer planets drift slowly so the system
    // reads as one coherent scale rather than four similarly paced dots.
    if(index==0) return 8.0;
    if(index==1) return 5.5;
    if(index==2) return 3.8;
    if(index==3) return 2.5;
    if(index==4) return 1.5;
    if(index==5) return 0.9;
    return 0.45;
}
float endOrbitDistance(int index) {
    if(index==0) return 8.0;
    if(index==1) return 14.0;
    if(index==2) return 28.0;
    if(index==3) return 48.0;
    if(index==4) return 78.0;
    if(index==5) return 118.0;
    return 175.0;
}
float endOrbitStart(int index) {
    if(index==0) return -2.15;
    if(index==1) return -1.15;
    if(index==2) return -1.8;
    if(index==3) return -0.62;
    if(index==4) return -1.4;
    if(index==5) return -0.9;
    return -2.0;
}
float endOrbitTilt(int index) {
    if(index==0) return 0.18;
    if(index==1) return 0.15;
    if(index==2) return 0.12;
    if(index==3) return 0.09;
    if(index==4) return 0.06;
    if(index==5) return 0.04;
    return 0.025;
}
float endSpinRate(int index) {
    // Even integer revolutions per 3600 seconds. This preserves the 3600 s
    // clock-reset invariant for 0.5x, 1x, and 2x END_ORBIT_SPEED.
    if(index==0) return 24.0;
    if(index==1) return 20.0;
    if(index==2) return 16.0;
    if(index==3) return 12.0;
    if(index==4) return 8.0;
    if(index==5) return 6.0;
    return 4.0;
}
vec3 endPlanetCenter(int index, float phase) {
    float radius=endOrbitDistance(index);
    float angle=endOrbitStart(index)+phase*endOrbitSpeed(index);
    float tilt=endOrbitTilt(index);
    return vec3(radius*cos(angle),12.0+radius*sin(angle)*sin(tilt),radius*sin(angle)*cos(tilt));
}
float endPlanetRadius(int index) {
    if(index==0) return 1.45;
    if(index==1) return 0.70;
    if(index==2) return 3.60;
    if(index==3) return 0.50;
    if(index==4) return 6.00;
    if(index==5) return 1.30;
    return 0.32;
}
// Closest positive intersection. Analytic intersections keep empty sky inexpensive.
float endSphere(vec3 ray, vec3 center, float radius) {
    float along=dot(ray,center);
    float perpendicular2=dot(center,center)-along*along;
    if(along<=0.0 || perpendicular2>=radius*radius) return 1e5;
    return along-sqrt(max(radius*radius-perpendicular2,0.0));
}
vec3 endPlanetSurface(vec3 n, int index, float spin) {
    // spin is an independent axial angle, not the orbital phase, so every
    // planet visibly rotates on its own while the orbital motion stays clean.
    vec3 p=vec3(cos(spin)*n.x+sin(spin)*n.z,n.y,-sin(spin)*n.x+cos(spin)*n.z);
    float terrain=endNoise(p*5.0)*0.7+endNoise(p*13.0)*0.3;
    if(index==0) {
        float craters=smoothstep(0.52,0.58,endNoise(p*18.0));
        vec3 rock=mix(vec3(0.16,0.15,0.14),vec3(0.42,0.40,0.37),terrain);
        return rock*(0.7+0.5*craters);
    }
    if(index==1) {
        float land=smoothstep(0.48,0.54,terrain);
        vec3 surface=mix(vec3(0.018,0.10,0.32),vec3(0.12,0.28,0.09),land);
        surface=mix(surface,vec3(0.72,0.87,0.93),smoothstep(0.78,0.94,abs(p.y)));
        float cloud=smoothstep(0.54,0.65,endNoise(p*9.0+vec3(4.0,0.0,0.0)));
        return mix(surface,vec3(0.85,0.90,0.95),cloud*0.85);
    }
    if(index==2) {
        vec3 rock=mix(vec3(0.18,0.038,0.015),vec3(0.64,0.25,0.085),terrain);
        return rock*(0.7+0.3*smoothstep(0.30,0.49,endNoise(p*22.0)));
    }
    if(index==3) {
        vec3 sand=mix(vec3(0.58,0.40,0.20),vec3(0.82,0.68,0.42),terrain);
        sand=mix(sand,vec3(0.95,0.92,0.88),smoothstep(0.72,0.96,abs(p.y)));
        return sand;
    }
    if(index==4) {
        float bands=0.5+0.5*sin(p.y*36.0+endNoise(p*8.0)*6.0);
        return mix(vec3(0.26,0.12,0.048),vec3(0.82,0.64,0.36),bands)*(0.8+terrain*0.4);
    }
    if(index==5) {
        float streaks=smoothstep(0.42,0.58,abs(endNoise(p*7.0)-0.5));
        vec3 ice=mix(vec3(0.10,0.34,0.52),vec3(0.52,0.78,0.92),terrain);
        return mix(ice,vec3(0.28,0.62,0.80),streaks*0.45);
    }
    float cracks=smoothstep(0.0,0.06,abs(terrain-0.50));
    return mix(vec3(0.055,0.25,0.36),vec3(0.48,0.78,0.88),cracks)*(0.7+terrain*0.5);
}
vec3 endPlanetGlowTint(int index) {
    if(index==0) return vec3(0.45,0.72,1.15);
    if(index==1) return vec3(0.45,0.72,1.15);
    if(index==2) return vec3(1.05,0.48,0.14);
    if(index==3) return vec3(1.00,0.70,0.30);
    if(index==4) return vec3(1.00,0.70,0.30);
    if(index==5) return vec3(0.35,0.82,1.05);
    return vec3(0.35,0.82,1.05);
}
float endPlanetGlowStrength(int index) {
    if(index==0) return 0.75;
    if(index==1) return 0.85;
    if(index==2) return 1.05;
    if(index==3) return 0.85;
    if(index==4) return 0.95;
    if(index==5) return 0.80;
    return 0.70;
}
vec3 endPlanetRimTint(int index) {
    if(index==0) return vec3(0.09,0.35,0.95);
    if(index==1) return vec3(0.09,0.35,0.95);
    if(index==2) return vec3(0.70,0.20,0.07);
    if(index==3) return vec3(0.62,0.42,0.15);
    if(index==4) return vec3(0.18,0.48,0.70);
    if(index==5) return vec3(0.12,0.52,0.78);
    return vec3(0.16,0.55,0.78);
}
// Soft exosphere scattering around a planet's silhouette. rho==1 is the limb:
// the glow peaks there, keeps a narrow rim over the outer part of the disk,
// and falls off in a wide haze outside. The lit side (facing the central star)
// scatters more, which reads as light spilling around the planet through dust.
vec3 endPlanetGlow(vec3 ray, vec3 center, float radius, vec3 star, int index) {
    vec3 offset=center-ray*dot(ray,center);
    float rho=length(offset)/radius;
    if(rho>6.0) return vec3(0.0);
    float d=rho-1.0;
    float limb=exp(-pow(d*2.2,2.0));
    float outside=exp(-max(d,0.0)*1.1);
    float inside=rho<1.0 ? exp(-max(-d,0.0)*1.8) : 1.0;
    vec3 closest=ray*dot(ray,center);
    vec3 outward=(closest-center)/max(length(offset),1e-5);
    vec3 toStar=normalize(star-closest);
    float lit=0.35+0.65*pow(max(dot(outward,toStar),0.0),1.05);
    return endPlanetGlowTint(index)*lit*endPlanetGlowStrength(index)*
           (0.28*limb+0.16*outside*inside);
}

vec3 endOrbitNormal(int index) {
    float tilt=endOrbitTilt(index);
    return normalize(vec3(0.0, -cos(tilt), sin(tilt)));
}

// Faint dust scattered along a planet's orbital path. The band is static in
// direction space, so it reads as a distant debris ring rather than a solid line.
vec3 endOrbitDust(vec3 ray, vec3 center, float orbitRadius, vec3 normal, float footprint) {
    float denom=dot(ray,normal);
    if(abs(denom)<0.001) return vec3(0.0);
    float t=dot(center,normal)/denom;
    if(t<=0.0) return vec3(0.0);
    vec3 local=ray*t-center;
    float r=length(local);
    float aa=max(footprint*t,0.05);
    float width=orbitRadius*0.012+0.22;
    float band=1.0-smoothstep(0.0,width,abs(r-orbitRadius));
    if(band<=0.0) return vec3(0.0);
    float dust=0.45+0.55*endNoise(local*0.55);
    float clumps=smoothstep(0.42,0.80,endNoise(local*1.8));
    float radial=0.72+0.28*sin(r*31.0);
    vec3 color=mix(vec3(0.18,0.16,0.20),vec3(0.34,0.30,0.34),dust);
    return color*band*dust*radial*(0.22+0.28*clumps);
}

// Single central wormhole: a dark event horizon with a bright photon ring and
// a dusty, tilted accretion disk. Planets use this object as their light source.
vec3 endWormhole(vec3 ray, vec3 center, float footprint) {
    float horizonRadius=1.05;
    if(endSphere(ray,center,horizonRadius)<1e4) return vec3(0.0);
    vec3 offset=center-ray*dot(ray,center);
    float rho=length(offset)/horizonRadius;
    float photon=exp(-pow((rho-1.0)*4.0,2.0));
    vec3 color=vec3(0.55,0.45,0.95)*photon*0.9;
    vec3 normal=normalize(vec3(0.28,1.0,0.18));
    float denom=dot(ray,normal);
    if(abs(denom)>0.001) {
        float t=dot(center,normal)/denom;
        if(t>0.0) {
            vec3 local=ray*t-center;
            float r=length(local);
            float aa=max(footprint*t,0.03);
            float inner=horizonRadius*1.5;
            float outer=horizonRadius*4.2;
            float disk=smoothstep(inner,inner+aa,r)*(1.0-smoothstep(outer,outer+aa,r));
            float dust=0.45+0.55*endNoise(local*0.7);
            float bands=0.65+0.25*sin(r*24.0)+0.10*sin(r*83.0);
            vec3 diskColor=mix(vec3(0.08,0.10,0.30),vec3(0.85,0.55,0.24),dust);
            color+=diskColor*disk*bands*0.42;
        }
    }
    return color;
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
    for(int i=0;i<7;++i) {
        sky+=endOrbitDust(ray,starCenter,endOrbitDistance(i),endOrbitNormal(i),footprint);
    }
    float nearest=endSphere(ray,starCenter,1.05);
    if(nearest<1e4) {
        sky=vec3(0.0);
    } else {
        sky+=endWormhole(ray,starCenter,footprint);
    }
    for(int i=0;i<7;++i) {
        vec3 center=endPlanetCenter(i,phase);
        float radius=endPlanetRadius(i);
        float hit=endSphere(ray,center,radius);
        if(hit<nearest) {
            vec3 n=normalize(ray*hit-center);
            vec3 light=normalize(starCenter-(ray*hit));
            float lit=max(dot(n,light),0.0);
            float spin=2.0*PI*fract(frameTimeCounter*END_ORBIT_SPEED*endSpinRate(i)/3600.0);
            vec3 surface=endPlanetSurface(n,i,spin);
            vec3 tint=endPlanetRimTint(i);
            float rim=pow(1.0-max(dot(n,-ray),0.0),3.0);
            float ambientLight=0.16;
            vec3 planet=surface*(ambientLight+lit*1.35)+tint*rim*(0.05+lit*0.25);
            float edge=radius-length(ray*dot(ray,center)-center);
            float coverage=smoothstep(0.0,max(footprint*hit,0.0001),edge);
            sky=mix(sky,planet,coverage);
            nearest=hit;
        }
    }
    // Second pass adds the atmosphere glow over the sky after disk coverage, so
    // halos stay visible around every silhouette while rings can still draw on
    // top of the giant's own glow below.
    for(int i=0;i<7;++i) {
        vec3 center=endPlanetCenter(i,phase);
        sky+=endPlanetGlow(ray,center,endPlanetRadius(i),starCenter,i);
    }
    // Intersect the giant's tilted ring plane, then depth-test against all spheres.
    vec3 center=endPlanetCenter(4,phase);
    vec3 ringNormal=normalize(vec3(0.20,1.0,0.32));
    float denom=dot(ray,ringNormal);
    if(abs(denom)>0.001) {
        float hit=dot(center,ringNormal)/denom;
        if(hit>0.0 && hit<nearest) {
            vec3 local=ray*hit-center;
            float r=length(local);
            float aa=max(footprint*hit,0.02);
            float giantRadius=endPlanetRadius(4);
            float ringInner=giantRadius*1.22;
            float ringOuter=giantRadius*2.6;
            float mask=smoothstep(ringInner-aa,ringInner+aa,r)*(1.0-smoothstep(ringOuter-aa,ringOuter+aa,r));
            float gap=smoothstep(0.10,0.20,abs(r-giantRadius*1.72));
            float bands=0.52+0.22*sin(r*54.0+endNoise(local*1.3)*4.0)+0.12*sin(r*131.0);
            float dust=0.45+0.55*endNoise(local*1.4);
            float clumps=smoothstep(0.45,0.82,endNoise(local*3.2));
            vec3 dustColor=mix(vec3(0.22,0.19,0.15),vec3(0.58,0.44,0.26),dust);
            vec3 light=normalize(starCenter-(ray*hit));
            float shade=endSphere(light,-local,giantRadius)<1e4 ? 0.28 : 1.0;
            sky=mix(sky,dustColor*bands*shade*(0.55+0.45*clumps),mask*gap*0.72);
        }
    }
#endif
    return sky;
}
#endif
#endif
