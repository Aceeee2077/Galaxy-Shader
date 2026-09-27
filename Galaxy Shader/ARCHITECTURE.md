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
| colortex7 | RGBA16F, persistent ping-pong | Resolved HDR history in RGB and normalized previous-frame view depth in A |
| depthtex0 | Loader depth | All depth-writing geometry |
| depthtex1 | Loader depth | Opaque scene used by screen effects and water |
| shadowtex0 | Loader depth | Orthographic shadow map, manual comparisons |

The geometry pass never samples colortex0–3. Water reads colortex4 only, avoiding read/write feedback and Iris atlas aliases. Deferred and composite programs rely on Iris ping-pong behavior. Metadata blending is disabled per attachment, while native color blending remains available to the game. With `separateAo=true`, terrain vertex alpha is explicitly consumed as AO, not opacity.

Format declarations are Iris metadata inside a multiline comment: the Iris preprocessor preserves comments and its CPU parser reads the symbolic format names there, while the GLSL compiler ignores them. The GPU verifier does not inject format definitions. A negative regression replays the old un-commented declarations and requires their compilation to fail before compiling the unchanged fixed source successfully.

## Pass sequence

1. **shadow**: matching vegetation animation, alpha cutout, omit transparent water/glass shadows.
2. **gbuffers**: forward HDR lighting with normal/specular material evaluation. Dedicated variants handle terrain, entities, block entities, hands, sky suppression, glint and beams. `gbuffers_weather` keeps Iris precipitation geometry but uses its own procedural wind-driven rain fragment program. Terrain wetness, roughness reduction and exposed-surface splash normals are written through the existing material attachments.
3. **deferred**: procedural sky including volumetric clouds, the rainbow term, the Overworld galaxy/nebula/aurora/shooting-star cosmic sky and the End rift core for clear depth; bounded AO/indirect sampling; screen-space colored light from visible emissive surfaces; glossy surface SSR; copy completed opaque scene to colortex4.
4. **transparent geometry**: water samples the opaque copy with a depth-tested refractive offset, absorption, Fresnel and an analytic sky reflection; `WATER_REFLECTIONS` can add screen-space hits on top. Rain adds expanding procedural normal rings and storm wind disturbance. Other translucent surfaces preserve their atlas alpha. Particles and precipitation render after deferred. Hands retain a post-process mask, including the transparent-hand path.
5. **composite**: dimension-aware height/valley/distance fog and shadow-sampled volumetric light. The reconstructed surface depth terminates fog and light integration at opaque terrain. Dawn/dusk shaft contrast is derived from variation between shadow-map samples; lightning contributes bounded scatter. Hand pixels bypass these effects. Fog density and scatter color use the same daily sky seed as the cloud field.
6. **composite1/2/3**: bright-pass downsampling and separable Gaussian blur at quarter width/height.
7. **composite4**: reproject and reject/clamp temporal history into colortex7; optional camera effects; restrained bloom; selectable Legacy Filmic/ACES-like/Natural Filmic mapping, color grading and gamma into colortex0. Natural Filmic uses a luminance-domain rational shoulder and gamut compression rather than the former log curve that lifted dark skies.
8. **final**: optional edge-adaptive FXAA on display RGB. Minecraft remains responsible for subsequent HUD/GUI rendering.

## Cost and stability choices

Version 1.12.1 aligns several budgets with the defaults of the reference pack the user supplied (Photon 1.3), reimplemented here from scratch: GTAO uses a 2-block world radius with 3x2 / 4x3 / 6x3 / 6x4 slices-per-steps across the AO profiles instead of 4x2 / 6x3 / 8x4; PCSS uses 0+4 / 3+6 / 4+10 / 6+12 / 8+16 blocker and filter taps instead of 0+4 / 6+8 / 8+12 / 12+16 / 16+24, so a lit fragment costs 14 shadow fetches at High rather than 20; water absorption is `WATER_ABSORPTION` = 0.39/0.14/0.07 per block through the water column and `WATER_ABSORPTION_UNDERWATER` = 0.20/0.08/0.04 while submerged; and volumetric light halves its sample count once the view rises above roughly 17 degrees, mirroring the reference pack's 20-step horizon / 4-step zenith shaft budget. The A/B run against 1.12.0 moves fullscreen draw time by -0.7% (clouds), -3.1% (sunset and daytime terrain), -1.1% (rain) and -2.1% (underwater); the shadow and AO changes also reduce geometry-pass and deferred work that this harness does not time. Underwater imagery changes by 2.99/255 on average because of the absorption coefficients; every other scenario stays under 0.09/255.

Version 1.12.0 replaces the End black hole with a rift core and rebalances several budgets. In the cloud march, `detail` is a per-sample level of detail derived from the sample index and a minimum distance: far samples keep two billow octaves plus the mean of the omitted one and their erosion term becomes its mean, and the 2D weather bank drops to four octaves, while near samples keep the full field. Direct-sky steps are 16/24/36 for Medium/High/Ultra, and the light march uses two longer samples (step 56) at High instead of three short ones so the integrated optical path length is preserved while a third of the density evaluations disappear. Sky reflection for water and glossy surfaces uses a single cloud sheet (`cloudSheet`) instead of a second volumetric march, so reflective pixels never pay for view-ray cloud integration. Water refraction is one displaced lookup plus at most one extra tap; the multi-tap blur survives only at the highest water profile, and the underwater distance blur is limited to that profile as well. Water reflections default to the analytic sky, with traced hits behind `WATER_REFLECTIONS` for Ultra/Cinematic. Water specular uses a single shadow tap instead of the PCSS blocker search. Volumetric light uses 8 samples per quality step (previously 10) and 3 per step underwater (previously 4); SSR budgets are 8/14/20/28 steps with a three-iteration refinement and one diagonal blur cross. The A/B run against 1.11.2 at 1280x720 HIGH measures 32-47% lower draw time across clouds, sunset, daytime terrain/water, rain and underwater, with a mean 8-bit difference below 1.2 and a 95th percentile of at most 4.

Version 1.11.2 separates cloud view detail from light-transport detail on Medium/High. Cloud silhouette/erosion view samples remain unchanged. Shadow density uses three weather octaves and two 3D billow octaves, replacing omitted fine detail by its mean; reflected sky uses 8/16 view samples while direct sky retains 16/32. Ultra/Cinematic retain the full shadow and reflected-cloud budgets. Out-of-layer density returns before evaluating weather/noise. Colored-light metadata rejection precedes depth fetch; indirect samples with zero facing/range skip normal/color fetches while retaining their original normalization weight.

`compare_performance.py` loads the prior release directly from ZIP, compiles both variants in one context, warms temporal history, and alternates A/B/B/A. OpenGL elapsed queries measure fullscreen draws and the water draw at 1280x720 HIGH; compilation, CPU readback, terrain rasterization and shadow rasterization are excluded. Each stage reports the median of 16 samples. The report includes before/after images, mean and 95th-percentile 8-bit differences. These isolated synthetic draw timings are not complete frame times or Minecraft FPS. The bundled comparison covers clouds, sunset, daytime terrain/water, rain and underwater.

Version 1.11.1 removes the six legacy End planets and all orbital dust tracks. The End sky now evaluates one giant sphere, one giant atmosphere and one ring plane, alongside the existing black hole and star field. The seven-body surface/glow loops and their per-body material/orbit tables are deleted. Ring detail noise is skipped outside its visible annulus. Overworld passes and quality budgets are unchanged; in-game FPS improvement has not been measured.

Version 1.11.0 uses eight-corner 3D value noise for cloud billows and edge erosion, 16/32/48 view samples at Medium/High/Ultra, and 2/3/4 expanding light samples. Distant clouds fade into atmospheric color; an eight-frame stratified phase reduces coherent march bands. The weather bank remains a cheap vertex shadow approximation. Cloud self-shadowing and multiple scattering are approximations, not a full atmospheric transport solver. End spheres and rings are depth ordered; ring frequencies are attenuated by their pixel footprint. The black hole uses analytic angular photon/back-disk/front-disk layers. End terrain lighting is independent of the planet visibility toggle and uses the shadow map. No extra render targets or dependencies were introduced.

TAA uses a persistent HDR/depth history, previous camera matrices, depth/screen/camera-cut rejection and a YCoCg neighborhood clamp. It intentionally does not jitter the projection or depend on per-object motion vectors. PCSS uses compile-time blocker/filter budgets with deterministic rotation. GTAO-style AO uses deterministic directional horizons, so it does not require a separate noisy AO buffer or blur pass. SSR rejects background/offscreen samples and returns a multi-factor confidence. Volumetrics integrate a finite distance and use frame-varying jitter only when TAA is enabled. Volumetric clouds ray-march the sky ray only when `CLOUD_QUALITY >= 2`; the low-profile path keeps the original single-plane fallback. Colored light is a screen-space gather of visible emissive surfaces and does not allocate voxel storage. No compute dispatch is used.

Profiles change real compile-time loop budgets. `WEATHER_QUALITY` controls procedural rain/ripple layers, while `TERRAIN_FOG_QUALITY` controls lowland fog noise; coherent zero-rain branches avoid evaluating ripple fields in clear weather. Lower profiles turn off expensive effect branches while retaining a complete rendering path. Shadows use fixed sample patterns and a 2-block shadow camera grid. The engine still controls shadow camera updates, culling and world-coordinate wrapping, which need in-game movement tests.

## Development and validation

Development tools live in the repository's `tools/`, outside the installable ZIP. Windows Python 3.10+ is required for WGL tests; rendering also uses NumPy and Pillow. Players do not need Python.

```powershell
python tools/build.py
python tools/validate.py
python tools/render_smoke.py
python tools/test_directives.py
python tools/test_format_compilation.py
python tools/test_tonemap.py
python tools/test_end_sky.py
python tools/render_reference.py
python tools/compare_performance.py --baseline "Galaxy Shader-1.11.1.zip"
python tools/check_iris_directives.py --iris path/to/iris.jar --libraries path/to/.minecraft/libraries
python tools/build.py --package
```

`validate.py` expands and checks includes, options, profile values, default HIGH equivalence, menu reachability, dimension entrypoints and draw-buffer declarations. It compiles and links on the real GPU for all profiles, all-off settings, forced PBR/camera effects, both LabPBR macro states and all dimension paths. Identical expanded programs are compiled once.

`render_smoke.py` rasterizes synthetic geometry, water and precipitation through the shipped programs, constructs real depth/shadow buffers, executes the post passes, checks framebuffer completeness and GL errors, reads back every post stage for finite pixels, rejects blank final outputs, and compares identical-frame replay and static-camera motion blur. It includes distinct clear, cloudy, rain, and thunder states. Its images are explicitly labeled synthetic; they are not gameplay evidence.

The build command rejects packaging if compile/render/Iris directive reports do not match the current shader SHA-256, or if only quick compilation was run. `check_iris_directives.py` executes the real Iris CPU directive parser in the supplied JAR; this catches configuration syntax that a GLSL driver accepts but Iris does not. ZIP contents are byte-checked against the source, CRC-checked, and verified to contain `shaders/` at the root. Reports and diagnostic images remain in `validation/`.
