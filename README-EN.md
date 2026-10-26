# Galaxy Shader

Galaxy Shader—Minecraft Java shaders, version **1.15.2**. On top of the bright warm palette it adds a rotating Milky Way sheet, procedural moon phases and three-band atmospheric sunlight: warm daylight, more readable outdoor shade, fixed exposure at 1.25 and saturation at 1.1 give foliage, wood and sky a more vivid look. See the [player guide](Galaxy%20Shader/README-EN.md) and [earlier parameter mapping](Galaxy%20Shader/REFERENCE-PHOTON.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

The latest installation package is `Galaxy Shader-1.15.2.zip` and its checksum. Reset shader settings before selecting HIGH; changing a quality profile alone does not reset saved exposure or saturation.

## Effect Preview

Warm palette comparison (synthetic GPU fixtures, 1.14.0 left, 1.14.1 right):

![Warm palette comparison](Galaxy%20Shader/previews/warm-palette.png)

In-game screenshots:

![Overworld effect](Galaxy%20Shader/previews/main.png)

End rift core and giant planet close-up (composited GPU preview):

![End planet sky](Galaxy%20Shader/previews/end-sky.png)

1.15.1 rotating night galaxy: rises from one side, crosses overhead near midnight, sets on the other side (synthetic GPU sky, not a gameplay capture):

![Rotating night galaxy](Galaxy%20Shader/previews/night-galaxy.png)

1.15.1 procedural moon: phases 0–7, maria and crater mottling, earthshine and halo, with moonlight scaled by the illuminated fraction (synthetic GPU sky):

![Procedural moon phases](Galaxy%20Shader/previews/night-moon.png)

1.15.1 warm sunlight: three-band atmospheric transmittance, a wider sunward twilight band and a warm-core / cool-fringe aureole (synthetic GPU fixtures, 1.14.1 left, 1.15.1 right):

![Warm sunlight comparison](Galaxy%20Shader/previews/warm-sun.png)

## Directory Structure

- `Galaxy Shader/`: MIT shader code (1.15.1), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.15.2.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).
