#ifndef SE_PBR
#define SE_PBR
struct Material { vec3 albedo; vec3 normal; vec3 f0; float roughness; float metal; float ao; float emission; };
Material defaultMaterial(vec3 albedo, vec3 n) {
    Material m;
    m.albedo=albedo; m.normal=n; m.f0=vec3(0.04); m.roughness=0.8;
    m.metal=0.0; m.ao=1.0; m.emission=0.0;
    return m;
}
vec3 metalF0(int id, vec3 albedo) {
    // Normal-incidence reflectance for the standard's named conductors.
    if(id==230) return vec3(0.56,0.57,0.58);
    if(id==231) return vec3(1.00,0.77,0.34);
    if(id==232) return vec3(0.91,0.92,0.92);
    if(id==233) return vec3(0.55,0.56,0.55);
    if(id==234) return vec3(0.95,0.64,0.54);
    if(id==235) return vec3(0.63,0.63,0.64);
    if(id==236) return vec3(0.67,0.64,0.59);
    if(id==237) return vec3(0.96,0.95,0.91);
    return albedo;
}
void decodeLabPBR(inout Material m, vec4 normalMap, vec4 specMap, mat3 tbn) {
    vec2 xy=normalMap.rg*2.0-1.0;
    // Iris tangents follow atlas V (downward), matching DirectX normal Y.
    vec3 tangentNormal=vec3(xy,sqrt(max(1.0-dot(xy,xy),0.0)));
    m.normal=safeNormalize(tbn*tangentNormal);
    m.ao=normalMap.b;
    m.roughness=max(pow(1.0-specMap.r,2.0),0.045);
    int code=int(floor(specMap.g*255.0+0.5));
    m.metal=step(230.0,float(code));
    m.f0=code>=230 ? metalF0(code,m.albedo) : vec3(specMap.g);
    m.emission=specMap.a<0.998 ? specMap.a*(255.0/254.0) : 0.0;
}
vec3 fresnelSchlick(vec3 f0, float cosine) { return f0+(1.0-f0)*pow(1.0-sat(cosine),5.0); }
vec3 specularBRDF(Material m, vec3 v, vec3 l) {
    vec3 h=safeNormalize(v+l);
    float nv=max(dot(m.normal,v),0.001), nl=max(dot(m.normal,l),0.0);
    float nh=max(dot(m.normal,h),0.0);
    float a2=m.roughness*m.roughness;
    float den=nh*nh*(a2-1.0)+1.0;
    float d=a2/(PI*den*den+1e-5);
    float k=(m.roughness+1.0)*(m.roughness+1.0)*0.125;
    float vis=1.0/max((nv*(1.0-k)+k)*(nl*(1.0-k)+k)*4.0,0.001);
    return min(d*vis*fresnelSchlick(m.f0,dot(v,h))*nl,vec3(16.0));
}
vec3 emissionTint(float id) {
    if(id==10102.0) return vec3(0.18,0.78,1.0);
    if(id==10103.0) return vec3(1.0,0.23,0.025);
    if(id==10104.0) return vec3(1.0,0.04,0.015);
    if(id==10105.0) return vec3(0.7,0.92,1.0);
    if(id==10106.0) return vec3(0.78,0.35,1.0);
    return vec3(1.0,0.58,0.20);
}
#endif
