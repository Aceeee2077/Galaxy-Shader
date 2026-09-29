# Galaxy Shader

Galaxy Shader--Minecraft Java Shaders, currently at the latest version **1.12.2**: the central celestial body in the End has been changed from a black hole/wormhole to a Rift Core (polyhedral crystal core, diffraction starburst, opposing jets, and a band of shattered stone shards), and the water surface and underwater performance cost has been reworked in the Photon direction—water reflections now default to analytic sky reflections (`WATER_REFLECTIONS` can optionally overlay screen-space hits), refraction is changed to a single offset sample, distant cloud layers automatically reduce detail, and reflections no longer perform a secondary march through volumetric clouds. 1.12.2 further adjusts the ambient occlusion radius/samples, PCSS shadow sampling range, per-block water absorption coefficient, and volumetric light zenith sampling with reference to Photon 1.3's default parameters. For player installation and feature descriptions, see [Galaxy Shader/README.md](Galaxy Shader/README.md); for the English version, see [README-EN.md](README-EN.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

The latest installation package is `Galaxy Shader-1.12.2.zip` and its checksum.

## Effect Preview

1.12.2 in-game screenshots:

![Overworld effect](Galaxy%20Shader/previews/main.png)

End rift core and giant planet close-up (composited GPU preview):

![End planet sky](Galaxy%20Shader/previews/end-sky.png)

## Directory Structure

- `Galaxy Shader/`: MIT shader source code (1.12.2), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.12.2.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).