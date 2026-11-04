# Galaxy Shader

Galaxy Shader—Minecraft Java shaders, version **1.15.51**. On top of the bright warm palette it adds a rotating Milky Way sheet, procedural moon phases, three-band atmospheric sunlight, anti-solar Earth shadow / Belt of Venus, zodiacal light with a night zodiacal band and gegenschein, night airglow, noctilucent clouds with crossed gravity-wave trains, thin-cloud iridescence, winter nacreous clouds, 22° ice-crystal halos with warm-to-cool spectral sun dogs that stretch into short pillars at a low sun, moon dogs, a lunar tangent arc and a lower tangent arc for a high sun, a 46° ring, circumhorizontal arc, circumzenithal arc, upper Parry arc, a parhelic circle and an anthelion, a thin-cloud lunar corona, Bishop's ring, stellar scintillation, star colour and gravity-wave airglow banding, an auroral zenith corona and curtain folds, a comet anti-tail, meteor persistent trains, a total-eclipse corona with red prominences, a rainy-night moonbow, a broad fog bow after rain, a sunset green flash, atmospheric refraction that lifts and vertically flattens a low sun or moon, and anti-solar ray spokes: warm daylight, more readable outdoor shade, fixed exposure at 1.25 and saturation at 1.1 give foliage, wood and sky a more vivid look. See the [player guide](Galaxy%20Shader/README-EN.md) and [earlier parameter mapping](Galaxy%20Shader/REFERENCE-PHOTON.md).

Target: Minecraft Java 26.2, Fabric, Iris, Sodium, OpenGL. FPS not yet tested.

From 1.15.32 the focus shifts to low-end performance: the HIGH preset keeps every visible effect, but work that is ultimately multiplied by zero (such as the night-sky layers at noon) is skipped, guarded by pixel-exact synthetic GPU regressions.

The latest installation package is `Galaxy Shader-1.15.51.zip` and its checksum. Reset shader settings before selecting HIGH; changing a quality profile alone does not reset saved exposure or saturation.

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

1.15.31 atmospheric refraction: a sun or full moon close to the horizon is lifted and compressed vertically, with its lower limb raised more than its upper one, so a low sun reads as a slightly flattened oval rather than a circle (synthetic GPU disk comparison, off left, on right, not a gameplay capture):

![Atmospheric refraction](Galaxy%20Shader/previews/atmospheric-refraction.png)

1.15.30 Bishop's ring: a very broad, faint dust aureole around the sun, warm brown-pink on its inner edge and fading to a cool pale blue outside, with a soft edge (synthetic GPU solar view, ring brightened for preview):

![Bishop's ring](Galaxy%20Shader/previews/bishops-ring.png)

1.15.29 thin-cloud iridescence: soft pastel diffraction fringes appear in high thin cloud near the sun, tightening toward the disk and forming coloured arcs inside broken cloud patches (synthetic GPU sky, fringes brightened for preview):

![Thin-cloud iridescence](Galaxy%20Shader/previews/cloud-iridescence.png)

1.15.28 aurora curtain folds: the auroral curtain bends into large hanging pleats, carrying its green lower band and violet upper band up and down together while the fine rays bunch and brighten where a fold gathers (synthetic GPU northern-sky comparison, same aurora with the option off on the left and on the right, preview gain):

![Aurora curtain folds](Galaxy%20Shader/previews/aurora-folds.png)

1.15.27 noctilucent wave trains: two crossed gravity-wave trains cut through the noctilucent sheet, their crests bending, stretching in perspective near the horizon and drifting slowly (synthetic GPU panorama, same cloud with the option off on the left and on the right, preview gain):

![Noctilucent wave trains](Galaxy%20Shader/previews/nlc-waves.png)

1.15.26 airglow gravity-wave ripples: faint horizontal bands appear in the night airglow layer, bending slowly across azimuth and drifting as a whole (synthetic GPU panorama, airglow brightened for preview):

![Airglow gravity-wave ripples](Galaxy%20Shader/previews/airglow-ripples.png)

1.15.25 star colour: every star gets a stable surface-temperature tint from warm orange through pale yellow to cool blue-white, with an independent brightness spread (synthetic GPU star field, stars enlarged for review):

![Star colour](Galaxy%20Shader/previews/star-colors.png)

1.15.24 total-eclipse corona and prominences: at totality, pale corona streamers, polar plumes and an equatorial belt spread around the black lunar disk, with a few red prominences on its limb (synthetic GPU eclipse close-up, corona preview gain):

![Total-eclipse corona and prominences](Galaxy%20Shader/previews/eclipse-corona.png)

1.15.23 meteor persistent train: after a bright meteor passes, a pale green afterglow lingers along its path for a few seconds, broken into slowly drifting knots (synthetic GPU night view, train preview gain):

![Meteor persistent train](Galaxy%20Shader/previews/meteor-train.png)

1.15.22 moon dogs and lunar tangent arc: a low bright moon lights plate ice crystals, adding a cool pair of vertical moon-dog smears at the 22° ring sides and a pale cap tangent to its top (synthetic GPU night panorama, ice-halo preview gain):

![Moon dogs and lunar tangent arc](Galaxy%20Shader/previews/moon-dogs.png)

1.15.21 comet anti-tail: while the comet is active, a very thin dust needle points sunward beside the ordinary dust tail, brightest near the head and fading quickly (synthetic GPU comet view, anti-tail preview gain):

![Comet anti-tail](Galaxy%20Shader/previews/comet-antitail.png)

1.15.20 auroral zenith corona: active curtains converge into radiating rays overhead (synthetic GPU fisheye zenith view, corona preview gain):

![Auroral zenith corona](Galaxy%20Shader/previews/aurora-corona.png)

1.15.19 fog bow: a broad, almost white 42° anti-solar arc in fog after rain, with only faint cool and warm rims (synthetic GPU fog panorama, bow preview gain):

![Fog bow](Galaxy%20Shader/previews/fogbow.png)

1.15.18 stellar scintillation: the same star field at two instants, each star flickering on its own phase (synthetic GPU night comparison, twinkle preview gain):

![Stellar scintillation](Galaxy%20Shader/previews/star-scintillation.png)

1.15.17 circumzenithal arc: a coloured sunward smile high in the sky at low sun, red below and violet above (synthetic GPU upper-sky panorama, arc preview gain):

![Circumzenithal arc](Galaxy%20Shader/previews/circumzenithal-arc.png)

1.15.16 lunar corona: compact pastel diffraction rings around a bright moon in thin cloud, blue-white inside and warmer outside (synthetic GPU night panorama, rings preview gain):

![Lunar corona](Galaxy%20Shader/previews/lunar-corona.png)

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

- `Galaxy Shader/`: MIT shader code (1.15.51), menus, and bundled documentation.
- `tools/`: entrypoint generation, GPU compilation, offscreen rendering, and deterministic packaging tools.
- `validation/`: version-controlled validation reports and test checklists; generated artifacts such as composited scene PNGs/GIFs are kept locally only and are not checked into the repository.
- `Galaxy Shader-1.15.51.zip` / `.sha256`: latest installation package and SHA-256 checksum.

For the development and validation workflow, see [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md).
