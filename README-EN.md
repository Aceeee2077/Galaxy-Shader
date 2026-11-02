# Galaxy Shader

Galaxy Shader—Minecraft Java shaders, version **1.15.15**. On top of the bright warm palette it adds a rotating Milky Way sheet, procedural moon phases, three-band atmospheric sunlight, anti-solar Earth shadow / Belt of Venus, zodiacal light with a night zodiacal band and gegenschein, night airglow, noctilucent clouds, winter nacreous clouds, 22° ice-crystal halos with a 46° ring and circumhorizontal arc, a rainy-night moonbow, a sunset green flash and anti-solar ray spokes: warm daylight, more readable outdoor shade, fixed exposure at 1.25 and saturation at 1.1 give foliage, wood and sky a more vivid look. See the [player guide](Galaxy%20Shader/README-EN.md) and [earlier parameter mapping](Galaxy%20Shader/REFERENCE-PHOTON.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

The latest installation package is `Galaxy Shader-1.15.15.zip` and its checksum. Reset shader settings before selecting HIGH; changing a quality profile alone does not reset saved exposure or saturation.

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

1.15.3 twilight optics: anti-solar Earth shadow / Belt of Venus, sunward zodiacal light and night airglow (synthetic GPU panorama, preview gain):

![Twilight optics](Galaxy%20Shader/previews/twilight-optics.png)

1.15.15 supernumerary arcs: thin pale green and pink fringes inside the primary's violet edge (synthetic GPU panorama, fringe preview gain):

![Supernumerary arcs](Galaxy%20Shader/previews/supernumerary-arcs.png)

1.15.14 secondary rainbow and Alexander's dark band: a colour-reversed arc outside the primary and a darker gap between them (synthetic GPU double-rainbow panorama, secondary preview gain):

![Secondary rainbow](Galaxy%20Shader/previews/secondary-rainbow.png)

1.15.13 lunar pillar: a cool vertical shaft drawn by a low moon (synthetic GPU night panorama, preview gain):

![Lunar pillar](Galaxy%20Shader/previews/moon-pillar.png)

1.15.12 parhelic circle: a faint white horizontal band at the sun's altitude (synthetic GPU panorama, preview gain):

![Parhelic circle](Galaxy%20Shader/previews/parhelic-circle.png)

1.15.11 46° halo and circumhorizontal arc: a faint outer ring plus the horizontal spectral band at high sun (synthetic GPU high-sky panorama, preview gain):

![46° halo and circumhorizontal arc](Galaxy%20Shader/previews/ice-halo-companions.png)

1.15.10 anti-solar rays: cloud-shadow spokes converging on the anti-solar point at low sun (synthetic GPU anti-solar panorama, preview gain):

![Anti-solar rays](Galaxy%20Shader/previews/antisolar-rays.png)

1.15.9 green flash: a thin green-teal rim on the top solar limb at sunset (synthetic GPU solar close-up, preview gain):

![Green flash](Galaxy%20Shader/previews/green-flash.png)

1.15.8 nacreous clouds: pastel pink, green and blue lenticular sheets in the winter twilight stratosphere (synthetic GPU panorama, preview gain):

![Nacreous clouds](Galaxy%20Shader/previews/nacreous.png)

1.15.7 zodiacal band and gegenschein: a faint silver ecliptic band and an anti-solar oval in the night sky (synthetic GPU panorama, preview gain):

![Zodiacal band and gegenschein](Galaxy%20Shader/previews/zodiacal-band.png)

1.15.6 moonbow: a faint silver arc about 42° from the anti-lunar point on a rainy full-moon night (synthetic GPU panorama, preview gain):

![Moonbow](Galaxy%20Shader/previews/moonbow.png)

1.15.5 ice crystal halos: a 22° ring around the sun or moon plus low-sun parhelia, an upper tangent arc and a pillar (synthetic GPU panorama, preview gain):

![Ice crystal halos](Galaxy%20Shader/previews/ice-halos.png)

1.15.4 noctilucent clouds: blue-white high cloud bands after sunset, strongest in summer and stretched by view perspective (synthetic GPU panorama, preview gain):

![Noctilucent clouds](Galaxy%20Shader/previews/noctilucent.png)

## Directory Structure

- `Galaxy Shader/`: MIT shader code (1.15.15), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.15.11.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).
