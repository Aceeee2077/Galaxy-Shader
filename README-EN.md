# Galaxy Shader

Galaxy Shader—Minecraft Java shaders, version **1.14.0**. Calibrated from the supplied Photon 1.3 defaults: a 2-degree solar radius, 80% cloud-shadow strength and fixed exposure. More neutral daylight, cool sky fill, lowland morning mist and blue-hour colors refine the natural lighting. See the [player guide](Galaxy%20Shader/README-EN.md) and [parameter mapping](Galaxy%20Shader/REFERENCE-PHOTON.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

The latest installation package is `Galaxy Shader-1.14.0.zip` and its checksum.

## Effect Preview

Before/after calibration (synthetic GPU fixtures, old on the left):

![Photon calibration](Galaxy%20Shader/previews/photon-calibration.png)

In-game screenshots:

![Overworld effect](Galaxy%20Shader/previews/main.png)

End rift core and giant planet close-up (composited GPU preview):

![End planet sky](Galaxy%20Shader/previews/end-sky.png)

## Directory Structure

- `Galaxy Shader/`: MIT shader code (1.14.0), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.14.0.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).
