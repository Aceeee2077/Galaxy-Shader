# Rendering architecture

The authored shaders use GLSL 330 compatibility input conventions. Iris translates these to its actual terrain/entity pipeline. All entrypoint wrappers include shared implementations; the root and `world0` select `DIMENSION 0`, `world-1` selects `-1`, and `world1` selects `1`. A missing custom dimension falls back to the root Overworld implementation.

## Coordinates

- `vPlayer` is camera-relative world-oriented position, reconstructed with `gbufferModelViewInverse`.
- Lighting normals, light directions, wind and reflection directions are world-oriented.
- Screen-space depth reconstruction and ray intersection use view space; projection uses the matching `gbufferProjection`.
- Absolute animation coordinates add `cameraPosition` to player space. Shadow geometry uses `shadowModelViewInverse`, not the camera inverse.
- Sun and moon positions come from Iris every frame. No fixed time-to-direction approximation is used.
- Depth uses the conventional OpenGL clip interval and clear depth 1. Iris 1.11.2 for 26.2 restores this convention when a shaderpack is active (verified against the official release bytecode).

## Attachments

| Buffer | Format | Content / ownership |
| --- | --- | --- |
| colortex0 | RGBA16F | Linear lit color; becomes display RGB only in composite4 |
| colortex1 | RGBA16F | Encoded world normal in RGB; linear roughness in A |
| colortex2 | RGBA16F | Linear base color; dielectric F0 or -1 metal marker in A |
| colortex3 | RGBA8 | Sky light, emission, hand mask, valid geometry |
| colortex4 | RGBA16F | Immutable lit opaque scene including procedural sky, copied by deferred |
| colortex5 | R11F_G11F_B10F, quarter width/height | Bright pass and final blurred bloom |
| colortex6 | R11F_G11F_B10F, quarter width/height | Horizontal blur intermediate |
| depthtex0 | Loader depth | All depth-writing geometry |
| depthtex1 | Loader depth | Opaque scene used by screen effects and water |
| shadowtex0 | Loader depth | Orthographic shadow map, manual comparisons |

The geometry pass never samples colortex0–3. Water reads colortex4 only, avoiding read/write feedback and Iris atlas aliases. Deferred and composite programs rely on Iris ping-pong behavior. Metadata blending is disabled per attachment, while native color blending remains available to the game. With `separateAo=true`, terrain vertex alpha is explicitly consumed as AO, not opacity.

Format declarations are Iris metadata inside a multiline comment: the Iris preprocessor preserves comments and its CPU parser reads the symbolic format names there, while the GLSL compiler ignores them. The GPU verifier does not inject format definitions. A negative regression replays the old un-commented declarations and requires their compilation to fail before compiling the unchanged fixed source successfully.

## Pass sequence

1. **shadow**: matching vegetation animation, alpha cutout, omit transparent water/glass shadows.
2. **gbuffers**: forward HDR lighting with normal/specular material evaluation. Dedicated variants handle terrain, entities, block entities, hands, sky suppression, glint, beams and weather.
3. **deferred**: procedural sky for clear depth; bounded AO/indirect sampling for valid opaque surfaces; glossy surface SSR; copy completed opaque scene to colortex4.
4. **transparent geometry**: water samples the opaque copy with a depth-tested refractive offset, absorption, Fresnel and reflections. Other translucent surfaces preserve their atlas alpha. Particles render after deferred. Hands retain a post-process mask, including the transparent-hand path.
5. **composite**: dimension-aware fog and shadow-sampled volumetric light. Hand pixels bypass these effects.
6. **composite1/2/3**: bright-pass downsampling and separable Gaussian blur at quarter width/height.
7. **composite4**: optional camera effects, restrained bloom, bounded smoothed exposure, Filmic, color grading and gamma.
8. **final**: edge-adaptive FXAA on display RGB. Minecraft remains responsible for subsequent HUD/GUI rendering.

## Cost and stability choices

No history color, TAA jitter, stochastic per-frame sample rotation, voxel allocation or compute dispatch is used. SSAO and SSR reject background and offscreen samples; SSR refines accepted intersections and fades at edges. Volumetrics integrate a finite distance and reuse one cloud attenuation estimate along each ray. Exposure gain is bounded even with no eye light.

Profiles change real compile-time loop budgets. Lower profiles turn off expensive effect branches while retaining a complete rendering path. Shadows use fixed sample patterns and a 2-block shadow camera grid. The engine still controls shadow camera updates, culling and world-coordinate wrapping, which need in-game movement tests.

## Development and validation

Development tools live in the repository's `tools/`, outside the installable ZIP. Windows Python 3.10+ is required for WGL tests; rendering also uses NumPy and Pillow. Players do not need Python.

```powershell
python tools/build.py
python tools/validate.py
python tools/render_smoke.py
python tools/test_directives.py
python tools/test_format_compilation.py
python tools/check_iris_directives.py --iris path/to/iris.jar --libraries path/to/.minecraft/libraries
python tools/build.py --package
```

`validate.py` expands and checks includes, options, profile values, default HIGH equivalence, menu reachability, dimension entrypoints and draw-buffer declarations. It compiles and links on the real GPU for all profiles, all-off settings, forced PBR/camera effects, both LabPBR macro states and all dimension paths. Identical expanded programs are compiled once.

`render_smoke.py` rasterizes synthetic geometry and water through the shipped programs, constructs real depth/shadow buffers, executes the post passes, checks framebuffer completeness and GL errors, reads back every post stage for finite pixels, rejects blank final outputs, and compares identical-frame replay and static-camera motion blur. Its images are explicitly labeled synthetic; they are not gameplay evidence.

The build command rejects packaging if compile/render/Iris directive reports do not match the current shader SHA-256, or if only quick compilation was run. `check_iris_directives.py` executes the real Iris CPU directive parser in the supplied JAR; this catches configuration syntax that a GLSL driver accepts but Iris does not. ZIP contents are byte-checked against the source, CRC-checked, and verified to contain `shaders/` at the root. Reports and diagnostic images remain in `validation/`.
