# Galaxy Shader

Galaxy Shader--Minecraft Java Shaders, currently at the latest version **1.12.3**: a clear sunrise or sunset no longer renders like overcast weather. The isotropic volumetric term and the unweighted shaft term were painting the whole sky with warm light at low sun angles, the dawn haze coefficients cut clear-morning visibility to about a quarter, and the cloud-coverage setting doubled as an overcast switch that dimmed the sunlight and sky with it. The sky-side isotropic term is now about an eighth of its old value, shafts use a forward phase weight, dawn haze is halved, and cloud coverage only adds clouds. 1.12.2 moved the End centrepiece from a black hole/wormhole to a Rift Core (polyhedral crystal core, diffraction starburst, opposing jets, and a band of shattered stone shards) and reworked water surface and underwater cost in the Photon direction—water reflections now default to analytic sky reflections (`WATER_REFLECTIONS` can optionally overlay screen-space hits), refraction is a single offset sample, distant cloud layers reduce detail automatically, and reflections no longer march volumetric clouds twice; it also adjusted the ambient occlusion radius/samples, PCSS range, per-block water absorption and volumetric zenith sampling against Photon 1.3's default parameters. For player installation and feature descriptions, see [Galaxy Shader/README.md](Galaxy Shader/README.md); for the English version, see [README-EN.md](README-EN.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

The latest installation package is `Galaxy Shader-1.12.3.zip` and its checksum.

## Effect Preview

In-game screenshots:

![Overworld effect](Galaxy%20Shader/previews/main.png)

End rift core and giant planet close-up (composited GPU preview):

![End planet sky](Galaxy%20Shader/previews/end-sky.png)

## Directory Structure

- `Galaxy Shader/`: MIT shader code (1.12.3), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.12.3.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).
