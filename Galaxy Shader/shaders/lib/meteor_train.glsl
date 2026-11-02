#ifndef SE_METEOR_TRAIN
#define SE_METEOR_TRAIN

// A bright meteor leaves a short-lived glowing train along its path. The
// train is a narrow cross-track Gaussian with slow knots, seeded per meteor so
// it stays stable while the head has already gone. Everything is analytic and
// exits after one plane-distance test.
vec3 meteorTrain(vec3 ray, vec3 head, vec3 tail, float life,
                 float seed, float time) {
    if (life <= 0.0) return vec3(0.0);
    vec3 pathDir = normalize(head - tail);
    vec3 planeNormal = cross(head, pathDir);
    float planeLength = length(planeNormal);
    if (planeLength < 1e-4) return vec3(0.0);
    planeNormal /= planeLength;
    float crossTrack = asin(clamp(dot(ray, planeNormal), -1.0, 1.0));
    if (abs(crossTrack) > 0.050) return vec3(0.0); // about 2.9 degrees

    float tailAngle = acos(clamp(dot(tail, pathDir), -1.0, 1.0));
    float headAngle = acos(clamp(dot(head, pathDir), -1.0, 1.0));
    float span = headAngle - tailAngle;
    float along = sat((acos(clamp(dot(ray, pathDir), -1.0, 1.0)) - tailAngle) /
                      (abs(span) > 1e-3 ? span : 1e-3));
    float width = 0.006 + 0.008 * along;
    float trail = exp(-pow(crossTrack / width, 2.0)) *
                  exp(-pow((along - 0.52) / 0.28, 2.0)) *
                  smoothstep(0.04, 0.18, along) *
                  (1.0 - smoothstep(0.84, 0.98, along));
    float knots = 0.70 + 0.30 * sin(along * 31.0 + seed * 19.0 + time * 0.55) *
                  (0.75 + 0.25 * sin(along * 67.0 - seed * 7.0));
    return vec3(0.34, 0.86, 0.64) * trail * knots * life * 0.55;
}
#endif
