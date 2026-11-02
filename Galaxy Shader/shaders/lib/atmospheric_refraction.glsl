#ifndef SE_ATMOSPHERIC_REFRACTION
#define SE_ATMOSPHERIC_REFRACTION

// Refraction near the horizon raises a celestial body and compresses it
// vertically, because the lower limb crosses denser air than the upper one.
// The lift below is about 0.55 degrees at the geometric horizon and fades over
// roughly the first fifteen degrees of elevation. The argument is the sine of
// elevation, which is already available at every call site; the small-angle
// difference from the angle itself only matters where the lift is negligible.
float refractionLift(float sinElevation) {
    return 0.0096 * exp(-15.0 * max(sinElevation, 0.0));
}
#endif
