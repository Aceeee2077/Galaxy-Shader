#ifndef SE_NOISE
#define SE_NOISE
float hash12(vec2 p) {
    vec3 q = fract(vec3(p.xyx) * 0.1031);
    q += dot(q, q.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
}
float valueNoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash12(i), hash12(i+vec2(1,0)), f.x),
               mix(hash12(i+vec2(0,1)), hash12(i+vec2(1,1)), f.x), f.y);
}
float fbm(vec2 p, int octaves) {
    float sum = 0.0, weight = 0.5;
    for (int i=0; i<6; ++i) {
        if (i>=octaves) break;
        sum += valueNoise(p)*weight;
        p = mat2(1.6,1.2,-1.2,1.6)*p+vec2(7.1,13.7);
        weight *= 0.5;
    }
    return sum;
}
vec2 diskSample(int i, int count) {
    float a = float(i)*2.39996323;
    return vec2(cos(a),sin(a))*sqrt((float(i)+0.5)/float(count));
}
#endif
