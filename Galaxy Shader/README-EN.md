# Galaxy Shader

**Photorealistic Minecraft Shader · 1.15.24 · Community Project**

**1.15.24 — total-eclipse corona and prominences (2026-11-02):** Once the Moon fully hides the solar photosphere, a pale corona opens around the black disk: curved streamers radiate outward, the belt is broader near the solar equator and narrows into fine plumes over the poles, while a few red prominences sit on the limb and shift slowly. It appears only around totality inside the existing eclipse window, is suppressed under overcast and leaves as soon as the eclipse ends. It shares the `CELESTIAL_EVENTS` schedule, with no new option. Analytic polar streamers, radial falloff and a limb-red Gaussian add no texture, lookup table or render target. The image below is a synthetic GPU eclipse close-up with the corona brightened for preview, not a gameplay capture.

![Total-eclipse corona and prominences (synthetic GPU eclipse close-up, corona preview gain)](previews/eclipse-corona.png)

**1.15.23 — meteor persistent train (2026-11-02):** After a bright meteor passes, its path does not snap back to darkness. A faint green afterglow lingers for a few seconds, wider and dimmer than the meteor itself, broken into slowly drifting knots, brightest around the middle and fading at both ends. It appears only during meteor events on a clear night, peaks after the meteor head has gone and then fades naturally. It shares `COSMIC_SKY_QUALITY`, `CELESTIAL_EVENTS` and the night/cloud gates, with no new option. An analytic path-plane Gaussian with two knot frequencies adds no texture, lookup table or render target. The image below is a synthetic GPU night view with the train brightened for preview, not a gameplay capture.

![Meteor persistent train (synthetic GPU night view, train preview gain)](previews/meteor-train.png)

**1.15.22 — moon dogs and lunar tangent arc (2026-11-02):** When a low, bright moon lights high plate ice crystals, the 22° lunar halo now gains a cool, vertically stretched moon dog on each side and a pale cap tangent to its top. Both appear only while the moon is below about 23°, stay near half the brightness of the equivalent solar parhelia and are visibly cooler; they fade as the moon climbs. They share the `ICE_HALOS` toggle, with no new option. Analytic azimuth/elevation Gaussians and a tangent-arc envelope add no texture, lookup table or render target. The image below is a synthetic GPU night panorama with the ice-halo brightness raised for preview, not a gameplay capture.

![Moon dogs and lunar tangent arc (synthetic GPU night panorama, ice-halo preview gain)](previews/moon-dogs.png)

**1.15.21 — comet anti-tail (2026-11-02):** While the comet is active, a very thin dust needle now points sunward beside the ordinary anti-sunward dust tail—larger grains spread along the orbital plane and read as a spike from near that plane. It is far narrower than the dust tail, brightest near the head, fades quickly with distance and does not appear behind the head. It shares the existing `CELESTIAL_EVENTS` schedule and the night/clear-sky gates, with no new option; an analytic tangent-plane Gaussian spike with a monotonic falloff adds no texture, lookup table or render target. The image below is a synthetic GPU comet view with the anti-tail brightened for preview, not a gameplay capture.

![Comet anti-tail (synthetic GPU comet view, anti-tail preview gain)](previews/comet-antitail.png)

**1.15.20 — auroral zenith corona (2026-11-02):** When the aurora is active, looking straight up now gathers the curtain into a corona of rays converging on the zenith: green toward the centre and shifting violet toward the fringe, rising and falling slowly with aurora strength and time. It shares `COSMIC_SKY_QUALITY`, `COSMIC_SKY_STRENGTH` and the existing cold-biome/storm gates, with no new option. It is a folded analytic azimuth pattern inside a soft zenith cap, adding no texture, lookup table or render target. The image below is a synthetic GPU fisheye view of the zenith with the corona brightened for preview, not a gameplay capture.

![Auroral zenith corona (synthetic GPU fisheye zenith view, corona preview gain)](previews/aurora-corona.png)

**1.15.19 — fog bow (2026-11-02):** Once rain has stopped but the air is still wet and cloudy, tiny fog droplets smear the refraction bow into a broad, almost white 42° anti-solar arc, leaving only a faint cool inner rim and warm outer rim. The sun must be behind the viewer and below about 42°, and the fog bow takes over from the coloured rain bow rather than sharing an active downpour. A new `FOGBOW` toggle (on by default, Weather page) controls it. It is an analytic radial band with a slight tint shift, adding no texture, lookup table or render target. The image below is a synthetic GPU fog panorama with the bow brightened for preview, not a gameplay capture.

![Fog bow (synthetic GPU fog panorama, bow preview gain)](previews/fogbow.png)

**1.15.18 — stellar scintillation (2026-11-02):** Stars no longer hold a constant brightness: turbulence in the lower atmosphere makes each one flicker quickly on its own phase and rate, and the swing grows near the horizon where the line of sight crosses more air. The effect is clearest late at night under a clear sky; cloud and moonlight still dim the field. A new `STAR_SCINTILLATION` slider (default 1.0, Atmosphere page) controls it, and 0 holds every star steady. Each star's phase comes from a stable hash, with no texture, lookup table or render target. The image below compares the same synthetic GPU star field at two instants with the twinkle swing raised for preview; it is not a gameplay capture.

![Stellar scintillation (synthetic GPU night comparison, twinkle preview gain)](previews/star-scintillation.png)

**1.15.17 — circumzenithal arc (2026-11-02):** When the sun sits below about 26°, plate crystals draw a bright coloured smile about 46° above it, its ends sagging toward the horizon and its centre near the zenith; red lines the lower edge and violet the upper, and the arc fades out above roughly 30° of solar elevation. It shares the `ICE_HALO_COMPANIONS` toggle with the 46° ring and circumhorizontal arc, adding no new option, and reuses the existing clear-ice visibility gate. It is an analytic Gaussian band with an azimuth envelope, adding no texture, lookup table or render target. The image below is a synthetic GPU upper-sky panorama with the arc brightened for preview, not a gameplay capture.

![Circumzenithal arc (synthetic GPU upper-sky panorama, arc preview gain)](previews/circumzenithal-arc.png)

**1.15.16 — lunar corona (2026-11-02):** A compact set of soft diffraction rings now surrounds a bright moon in thin cloud, about 2°–8° in radius, leaning blue-white near the disk and warmer outside. The rings scale with the illuminated moon fraction and night brightness, fade under overcast and are suppressed further in rain. A new `LUNAR_CORONA` toggle (on by default, Atmosphere page) controls them. Unlike ice halos, a corona comes from diffraction by cloud droplets rather than refraction by crystals, so it does not depend on `ICE_HALOS`. It is an analytic radial cosine with a soft envelope, adding no texture, lookup table or render target. The image below is a synthetic GPU night panorama with the ring brightness raised for preview, not a gameplay capture.

![Lunar corona (synthetic GPU night panorama, rings preview gain)](previews/lunar-corona.png)

**1.15.15 — supernumerary arcs (2026-11-02):** A few very thin pale green and pink fringes now appear a couple of degrees inside the violet edge of the primary bow—interference between the rays that form it, also called supernumerary arcs. They stay inside the narrow band where the bow is already fading and disappear outside it; rain or wetness, solar elevation and overcast gate them like the primary. They join the existing weather/rainbow system with no new option and are a damped analytic cosine, adding no texture, lookup table or render target. The image below is a synthetic GPU panorama with the fringe brightness raised for preview, not a gameplay capture.

![Supernumerary arcs (synthetic GPU panorama, fringe preview gain)](previews/supernumerary-arcs.png)

**1.15.14 — secondary rainbow and Alexander's dark band (2026-11-02):** About 9° outside the primary bow, a fainter secondary arc now appears with its colours reversed—red inside and violet outside. The sky between the two bows is slightly darker than on either side, forming Alexander's dark band. The secondary bow appears only during rain or lingering wetness, with the sun above the horizon and the sky not fully overcast; it stays near a tenth of the primary brightness. It joins the existing weather/rainbow system with no new option and is analytic angle work, adding no texture, lookup table or render target. The image below is a synthetic GPU double-rainbow panorama with the secondary bow brightened for preview, not a gameplay capture.

![Secondary rainbow and Alexander's dark band (synthetic GPU double-rainbow panorama, secondary preview gain)](previews/secondary-rainbow.png)

**1.15.13 — lunar pillar (2026-11-02):** A bright low moon also draws a narrow, faint cool shaft from the same plate crystals, rising from the disk with a short reflection below it; the shaft weakens as the moon climbs and disappears above about 20°. It shares the `ICE_HALOS` toggle, with no new option, stays at about half the solar pillar brightness and never adds sun dogs or a tangent arc. Everything is analytic angle work, with no texture, lookup table or render target. The image below is a synthetic GPU night panorama with preview gain, not a gameplay capture.

![Lunar pillar (synthetic GPU night panorama, preview gain)](previews/moon-pillar.png)

**1.15.12 — parhelic circle (2026-11-02):** A very faint white horizontal band crosses the sky at the sun's own altitude, passing through the sun dogs and continuing all the way around; it is a little brighter beside the sun and near the 120° parhelia. Plate ice crystals produce it, so it shares the clear ice-crystal weather of the 22° halo, 46° halo and circumhorizontal arc and disappears below the horizon. It joins the Atmosphere → 46° halo & arc toggle, with no new option; everything is analytic angle work, with no texture, lookup table or render target. The image below is a synthetic GPU panorama with preview gain, not a gameplay capture.

![Parhelic circle (synthetic GPU panorama, preview gain)](previews/parhelic-circle.png)

**1.15.11 — 46° halo and circumhorizontal arc (2026-11-02):** Beyond the 22° halo, a wider and fainter 46° ice-crystal ring now shows a red inner edge and a blue outer edge. Once the sun climbs above roughly 58°, horizontally aligned plate crystals instead light the circumhorizontal arc: a spectral band about 46° below the sun, spanning the sky, red on its upper edge and blue-violet below, brightest on either side of the solar azimuth. Both appear only in clear ice-crystal weather and exit early for a low or rainy sun. A new Atmosphere → 46° halo & arc toggle defaults to on. Everything is analytic angle work; no texture, lookup table or render target is added. The image below is a synthetic GPU high-sky panorama with preview gain, not a gameplay capture.

![46° halo and circumhorizontal arc (synthetic GPU high-sky panorama, preview gain)](previews/ice-halo-companions.png)

**1.15.10 — anti-solar rays (2026-11-02):** When the sun sits near the horizon, a very faint fan of light and dark spokes converges on the anti-solar point in the opposite half of the sky—cloud shadows seen in perspective. The fan appears only between about −6° and +14° solar height, exits immediately across the sunward half, leaves a dark core at its own focus and fades under overcast. A new Atmosphere → Anti-solar rays toggle defaults to on. Everything is analytic angle work with a little procedural noise; no texture, lookup table or render target is added. The image below is a synthetic GPU anti-solar panorama with preview gain, not a gameplay capture.

![Anti-solar rays (synthetic GPU anti-solar panorama, preview gain)](previews/antisolar-rays.png)

**1.15.9 — green flash (2026-11-02):** In the last degree before sunset or the first after sunrise, a thin green-teal rim appears on the top limb of the sun. It covers only the upper half of the disk and slightly dims the warm disk underneath, so the additive colour is not washed out by the highlight; a high, fully set or cloudy sun produces none. A new Atmosphere → Green flash toggle defaults to on. Everything is analytic angle work; no texture, lookup table or render target is added. The image below is a synthetic GPU solar close-up with preview gain, not a gameplay capture.

![Green flash (synthetic GPU solar close-up, preview gain)](previews/green-flash.png)

**1.15.8 — nacreous clouds (2026-11-02):** In the winter twilight, soft lenticular sheets appear high in the stratosphere, diffracting into a pastel pink, green and blue nacre. They are most visible near the horizon and fade upward. The layer appears only while the sun is about 2°–13° below the horizon, is much stronger in winter and needs clear weather; it differs from the noctilucent layer in altitude, season and colour. A new Clouds → Nacreous clouds toggle defaults to on. Everything is analytic noise plus three phase-offset cosines; no texture, lookup table or render target is added. The image below is a synthetic GPU panorama with preview gain, not a gameplay capture.

![Nacreous clouds (synthetic GPU panorama, preview gain)](previews/nacreous.png)

**1.15.7 — zodiacal band and gegenschein (2026-11-02):** After astronomical twilight the zodiacal dust reads as a faint silver band along the ecliptic, with a brighter oval gegenschein around the anti-solar point. The oval is longer along the ecliptic than across it, reads warmer than the band and fades near the horizon. The ecliptic is approximated by the plane through the sun direction and the celestial rotation axis; the outer band is cool and the spot warm. A new Atmosphere → Zodiacal band / gegenschein toggle defaults to on. The layer appears only once the sun is about 7° below the horizon, clouds suppress it and all of it is analytic angle work. The image below is a synthetic night-sky GPU panorama with preview gain, not a gameplay capture.

![Zodiacal band and gegenschein (synthetic night-sky GPU panorama, preview gain)](previews/zodiacal-band.png)

**1.15.6 — moonbow (2026-11-02):** On a rainy night with the moon above the horizon, a faint silver arc appears about 42° from the anti-lunar point. It shares the solar bow's refraction geometry and post-rain moisture, but its colour is almost fully desaturated and cooled, retaining only a trace of spectral order; brightness follows the illuminated moon fraction. A new moon or dry air removes it. A new Weather → Moonbow toggle defaults to on. Everything is analytic angle work; no texture, lookup table or render target is added. The image below is a synthetic rainy-night GPU panorama with preview gain, not a gameplay capture.

![Moonbow (synthetic rainy-night GPU panorama, preview gain)](previews/moonbow.png)

**1.15.5 — ice crystal halos (2026-11-02):** Cirrus ice crystals draw a fine ring about 22° from the sun or moon, red on the inner rim and blue outside. With a low sun, vertically stretched parhelia appear on both sides, an upper tangent arc caps the ring and a pillar rises from the horizon. The moon keeps only the circular ring; it produces no parhelia or pillar. A new Atmosphere → Ice crystal halos toggle defaults to on. Everything is analytic angle work, and sky pixels farther than about 35° from the light exit before any trigonometry; no texture, lookup table or render target is added. The image below is a synthetic GPU panorama with preview gain, not a gameplay capture.

![Ice crystal halos (synthetic GPU panorama, preview gain)](previews/ice-halos.png)

**1.15.4 — noctilucent clouds (2026-11-02):** After sunset, when the lower sky is dark but the mesosphere is still sunlit, blue-white high cloud bands with slow wave structure appear above the horizon. The layer is projected onto a horizontal plane, so it stretches in perspective and fades toward the zenith. It is strongest in summer and appears only in the roughly -3° to -26° solar window, in clear weather and at low elevation, correctly veiling stars and the Milky Way. A new Clouds → Noctilucent clouds toggle defaults to on. Everything is analytic noise; no texture, lookup table or render target is added. The image below is a synthetic GPU panorama with preview gain, not a gameplay capture.

![Noctilucent clouds (synthetic GPU panorama, preview gain)](previews/noctilucent.png)

**1.15.3 — twilight optics (2026-11-02):** Adds the anti-solar Earth's shadow and Belt of Venus, a sunward zodiacal-light cone and night airglow. Just after sunset the anti-solar horizon first darkens under a cool blue-grey shadow wedge, capped by a narrow pink-violet belt; the zodiacal light then opens as a silver-yellow cone above the sun's set point, widening and fading with elevation; after full darkness a slow green-teal airglow layer appears around 10° elevation. All three share one Atmosphere → Twilight optics strength slider (default 1), and cloud or storm cover suppresses them. Everything is evaluated analytically from angles and procedural noise, with no texture, lookup table or render target. The image below is a synthetic GPU panorama with preview gain applied; it is not a gameplay capture.

![Twilight optics (synthetic GPU panorama, preview gain)](previews/twilight-optics.png)

**1.15.2 — torch flicker fix:** Material IDs now use flat interpolation, preventing floating-point interpolation errors from toggling torch emission. Other effects and settings are unchanged.

Galaxy Shader is a bright, warm-color shader pack for Minecraft Java Edition. It uses OpenGL rasterization, shadow mapping, and screen-space effects while keeping block outlines readable. No compilation step is required, no external noise textures are needed, and no extra resource pack is required.

**1.15.1 — night sky and warm sunlight:** Adds one continuous Milky Way sheet bound to the day/night rotation, analytic moon phases 0–7, and solar colour from three-band atmospheric transmittance driven by solar elevation. Low sun turns amber rather than magenta, the twilight band spreads wider toward the sun, and the aureole graduates from a warm core to a cool fringe. No menu options are added; the warm exposure, saturation and shade-fill defaults from 1.14.1 are unchanged.

After updating, **reset shader settings**, then select HIGH. Quality profiles alone do not reset saved exposure or saturation. Synthetic GPU checks passed; Minecraft gameplay appearance and FPS remain unverified.

**1.15.1 — rotating night galaxy (2026-10-26):** The Milky Way is now one continuous sheet bound to the day/night rotation. It rises from one horizon at dusk, crosses overhead near midnight and sets on the opposite side. Its structure follows wide-field sky photographs: a cool blue-white star sheet, a warm central bulge, a branched dust lane and Great Rift, sparse pink H-alpha regions and fine unresolved stars. Everything is analytic noise; no textures, tables or extra render targets are added. The pattern is anchored in the star-fixed frame, so the whole sheet rotates rigidly and never flickers. It develops after twilight and dims toward the horizon through atmospheric extinction. The default 0.25 strength is now more readable than the old band; adjust it under Cosmic Sky → Galaxy / aurora strength. Aurora and event strengths are unchanged. The image below is a synthetic GPU sky, not a gameplay capture.

![Rotating night galaxy (synthetic GPU sky, four phases × four azimuths)](previews/night-galaxy.png)

**1.15.1 — procedural moon phases (2026-10-26):** The night moon is now analytic: phases 0–7, a soft terminator, maria and crater mottling, faint earthshine and a cool halo around the limb. Directional moonlight follows the illuminated fraction — brightest at full moon and nearly absent at new moon — and rain or thunderstorms dim the disk. The disk and halo are evaluated from the view direction only, with no textures or extra render targets. The image below shows a full-moon night and phases 0–7 (synthetic GPU sky, not a gameplay capture).

![Procedural moon phases and full-moon night (synthetic GPU sky)](previews/night-moon.png)

**1.15.1 — warm sunlight (2026-10-26):** Solar colour now comes from a three-band atmospheric transmittance: Rayleigh scattering, Mie extinction and ozone absorption are integrated with solar elevation, so a low sun turns naturally amber. Ozone retains enough green to keep the sky from drifting magenta. The twilight warm band spreads wider toward the sun, and the solar aureole graduates from a warm core to a cool fringe while direct-light brightness and shade contrast stay unchanged. Everything is analytic; no textures, lookup tables or render targets are added. The image below is a 1.14.1 (left) versus 1.15.1 (right) synthetic A/B, not a gameplay capture.

![Warm sunlight comparison (synthetic GPU fixtures, 1.14.1 left, 1.15.1 right)](previews/warm-sun.png)

The following notes describe earlier releases; the installed package you run remains authoritative.

**1.14.1 — bright warm palette:** Warm golden daylight replaces the neutral sun, sky fill loses its strong blue bias and outdoor shade receives more sky and ground bounce. Fixed exposure defaults to **1.25**, saturation to **1.1**, with contrast at **1**. White balance runs before tone mapping so bright neutral surfaces approach white smoothly. Foliage stays green, the sky stays blue, and sky-light/AO gates still reject outdoor bounce in closed caves. No extra texture samples or march steps are added.

![Warm palette comparison (synthetic GPU fixtures, 1.14.0 left, 1.14.1 right)](previews/warm-palette.png)

**1.14.0 — Photon parameter calibration:** The supplied Photon 1.3 defaults inform a 2-degree sun radius shared by the visible disk and PCSS penumbra, 0.8 cloud-shadow strength and fixed exposure at 1. Daylight changes chroma with solar elevation; cool sky fill and a small warm bounce shape outdoor shade. Low morning mist halves every seven blocks above Y=69. Warm twilight is more local, with a blue dome and pink horizon after sunset.

Reset all settings before selecting HIGH. Selecting a profile alone does not reset personal sun-radius, cloud-shadow or exposure settings. New controls are Lighting → Sun angular radius and Clouds → Cloud shadow strength. See the [parameter mapping](REFERENCE-PHOTON.md).

![Calibration before/after (synthetic GPU fixtures, old on the left)](previews/photon-calibration.png)

**1.13.1 — sunny daylight:** Low-angle sunlight previously suffered both air-mass attenuation and a horizon fade while diffuse sky fill stayed strong. This update removes the double suppression, strengthens and gently warms direct sunlight, and confines warm twilight scattering closer to the sun and horizon. Sunlit grass, wood and leaf edges separate more clearly from cool shade. A compact aureole surrounds the solar disk and remains behind clouds. Volumetric visibility moments now share optical-weight normalization, preventing uniformly lit air from generating artificial shafts. Rain still attenuates direct light.

**Sunrise / sunset:** Low solar elevations produce an amber lower sky, depth-dependent golden mist and a wave-broken solar path on water. The golden atmosphere fades out by a sun elevation of about 13 degrees. `DAWN_HAZE` controls the extra dawn mist (default 1); 0 removes that mist while retaining sunrise sky colours.

Reset settings and start with HIGH. `SUN_INTENSITY=1.0` already uses the new sunny calibration; try 0.75 for softer lighting or 1.25 for stronger sunlight. Keep exposure at 1.0. Previews are synthetic; gameplay appearance remains to be checked.

![Sunny preview (synthetic; clouds disabled to inspect solar glow)](previews/sunlight.png)

**1.13.0 — natural lighting, inspired by Photon:** Daylight is more neutral at noon and attenuates with low sun elevation. Surfaces, water and volumetric clouds share a directional sky-fill model; shadowed faces keep cool detail, and foliage gains shadow-constrained transmission. A thin high cloud layer sits behind cumulus. PCSS derives penumbra from world-space blocker separation. Clear dawn haze is lighter, and terrain fog no longer overlays the sky a second time. Water uses an IOR of 1.333, clearer shallows and blue-green depth; shoreline foam responds to lighting. Galaxy/aurora strength defaults to 25%, while stars and the End sky retain their identity. Soft-knee bloom and gently desaturated highlights keep bright surfaces restrained. These effects are implemented independently in this project.

New controls: `SKYLIGHT_STRENGTH` (Lighting, default 1), `SHADOW_SOFTNESS` (Shadows, 1.25), `WATER_CLARITY` (Water, 1), `BLOOM_STRENGTH` (Post Processing, 1), and `COSMIC_SKY_STRENGTH` (Cosmic Sky, 0.25). Cosmic Sky and Seasons are now reachable from the root menu. Reset to defaults or start with HIGH after installation, then adjust to taste; higher water clarity reduces absorption.

1.13.0 synthetic GPU preview (not a Minecraft capture):

![Natural lighting preview](previews/photon-style.png)

**1.12.3 — clear-morning fix:** A clear sunrise or sunset no longer renders like overcast weather. Three terms independent of the sun elevation were brightening the whole sky: the isotropic constant in the volumetric light, the shaft term that carried no view-direction weight, and the dawn haze coefficients, which cut clear-morning visibility to roughly a quarter. On top of that, the cloud-coverage setting doubled as an overcast switch and dimmed the sunlight and sky with it. The sky-side isotropic term is now about an eighth of its old value, shafts are weighted by a forward phase (`0.10 + 0.90·cos²`, so sunward god rays are unchanged), dawn height/valley fog density and the warm-haze blend are halved, cloud coverage only adds clouds while the density threshold and cirrus weight are tightened, and the warm atmospheric band stays near the horizon on the sun's side. New Atmosphere-page option `DAWN_HAZE` (0 / 0.5 / 1 / 1.5 / 2, default 1): 0 is a crisp clear sky, 2 restores a heavy morning fog bank.

**1.12.1 — parameter alignment against Photon 1.3 defaults:** Ambient occlusion now uses a 2-block world radius with 12 samples at High instead of 18; PCSS shadows follow the reference pack's "three blocker samples plus six to twelve filter taps" range, cutting a lit fragment from 20 to 14 shadow fetches; water adopts its per-block absorption coefficients (water column 0.39/0.14/0.07, underwater 0.20/0.08/0.04) so deep water keeps its blue-green instead of crushing to black and underwater visibility improves; volumetric light mirrors the reference shaft budget by halving its samples once the view is well above the horizon. Every one of these is an equivalent parameter reimplemented here - no Photon code was copied.

**1.12.0 — End rework and Photon-style performance pass:** The End centrepiece is no longer a black hole or wormhole. The former event horizon, photon ring and accretion disk are replaced by a **rift core**: a faceted crystal core, four long diffraction streaks, two counter-facing plasma jets, and two belts of shattered shards driven by angular sectors (each shard hashes its own radius, thickness and tint, and some sectors stay empty). The silhouette is spiked and segmented rather than a round horizon with a smooth dust disk. The giant's limb glow and ring dust move to cold violet-silver tones to match the new ambient light. Budgets across reflections, clouds, water and volumetrics were rebalanced: clouds drop fine noise detail in the far part of the march and use 16/24/36 direct-sky steps, with two longer light samples replacing three short ones; reflections use a single cloud sheet instead of a second volumetric march; water reflects the analytic sky by default and optional screen-space hits moved to the new `WATER_REFLECTIONS` option (on for ULTRA/CINEMATIC); water refraction is one displaced lookup plus at most one extra tap. Cumulative 1280x720 HIGH A/B against 1.11.2: clouds -37.2%, sunset -37.3%, daytime terrain/water -36.9%, rain -51.0%, underwater -36.6%; mean 8-bit difference 0.73-1.18 for clouds/sunset/day/rain and 2.99 underwater (the visible result of the absorption change), and the water draw itself is roughly 90% cheaper. Report: `validation/performance-report.json`; this is not Minecraft FPS.

**1.11.2 — Overworld performance:** Preserves direct-sky cloud detail, shadow resolution, volumetric light and SSR. Medium/High cloud shadows use low-frequency density with mean fine-detail compensation; reflected clouds use half the view steps. Colored light rejects non-emissive samples first, and indirect light skips zero-contribution shading.

**1.11.1 / 1.11.0:** Removes the six legacy End planets and their orbital dust tracks, leaving the ringed giant, the central object and a fixed starfield, and upgrades clouds to three-dimensional billows with edge erosion. The black hole centrepiece of those releases was replaced by the rift core in 1.12.0.

Start with HIGH; use ULTRA for finer clouds. Golden-hour rays require low sunlight and scene occluders. Bundled previews are synthetic GPU renders of the actual shaders, not Minecraft captures or a claim of pixel-identical reference matching.

## Delivery status

The first feature set is implemented and has passed standalone GPU compilation and synthetic-scene render checks. Full in-game acceptance on Minecraft + Iris and measured FPS data are still pending. No claim is made about every GPU or mod combination.

## Previews

1.12.1 synthetic GPU views (not Minecraft captures):

![Overworld](previews/main.png)

**1.5.0 — weather and atmosphere update:** Adds a dedicated procedural precipitation pass that uses the game's rain geometry while replacing its visible streaks with wind-driven layers, near/far density, and lightning response. Water receives multi-scale expanding and fading ripple rings; upward, sky-exposed block surfaces receive small splash impacts. Stone, paths, wood, and foliage darken smoothly with Iris `wetness`, lose roughness, and gain reflections. Clouds, sky, sun, fog, terrain, water, and volumetric accumulation now respond together to Clear / Cloudy / Rain / Thunderstorm. Dawn/dusk volumetrics ray-march the shadow map and use alternating lit/occluded samples to form shafts through canopy gaps, with automatic midday reduction and an energy cap. Terrain fog combines height fog, lowland/valley noise, and distance haze, stopping at scene depth so foreground walls remain opaque.

**1.6.0 — volumetric clouds, colored light, rainbow, and daily sky variation:** Overworld clouds are upgraded to a ray-marched volumetric field whose base and thickness respond to rain/storms, with forward self-shadowing and silver-lining scatter; low presets keep the single-plane fallback. Emissive blocks now project screen-space colored light onto visible geometry, controlled by `COLORED_LIGHT_QUALITY`. A post-rain rainbow was added, and sky, cloud coverage, and fog density now vary by calendar day.

**1.7.0 — cosmic sky and End planet update:** The End planetary system now has seven planets with dramatically spread orbits, obvious near/far apparent size and orbital-speed differences, and axial rotation decoupled from orbital motion. The Overworld night sky gains a tilted Milky Way band with colored nebulas, low northern aurora, occasional shooting stars, and a distant banded planet, controlled by `COSMIC_SKY_QUALITY`.

**1.7.1 — aurora and shooting-star tuning:** Removes the faint distant planet from the Overworld night sky; the northern aurora is brighter, taller, and more layered, and shooting stars occur more often.

**1.7.2 — softer lighting:** Reduces automatic exposure gain, direct sun intensity, daytime ambient light, and block light, while raising the bloom threshold and lowering bloom strength for a gentler, less blown-out image.

**1.7.3 — volumetric cloud blending:** Reworks the cloud density curve with a wider soft threshold and two soft vertical lobes, adds sky ambient color and horizon/distance soft transitions, and removes the hard detail cutouts for a more integrated sky.

**1.7.4 — water and underwater visibility:** Rain/wind now blur the refracted underwater background and raise surface reflection, making it harder to see into water from land. Underwater vision gains distance blur and stronger absorption, so the surface and land lose focus and become murkier with depth.

**1.8.0 — seasons:** Adds `SEASON_MODE` (Auto / Spring / Summer / Autumn / Winter) and `SEASON_STRENGTH`. Auto follows the calendar year and continuously drives sky, sunlight, ambient light, fog, cloud coverage, and foliage color; a specific season can also be forced for screenshots or themed worlds.

**1.8.1 — End celestial rework:** The seven planets now have far stronger orbit-distance and size contrast, with dust trails along each orbit. Planet night sides receive ambient fill so they no longer read as black holes. The central star is replaced by a single wormhole (dark event horizon, photon ring, and tilted dusty accretion disk), and the ringed giant's rings use layered radial bands and noise clumps instead of a solid ring.

**1.9.0 — celestial events and biome atmosphere:** Adds `CELESTIAL_EVENTS`: calendar-driven meteor showers, comets, aurora storms, a solar eclipse and a rare supernova. Adds `BIOME_BLEND`: temperature and rainfall now shift regional mood — warm desert haze, humid jungle/swamp fog, and colder blue light with stronger aurora in cold biomes.

**1.9.1 — water and cave depth:** Underwater gains blue-green god rays and flowing caustics, shorelines gain wind-driven foam, and water refraction uses stronger depth parallax. Caves gain a faint bioluminescent ambient and drifting motes for more depth in the dark.

**1.10.0 — particles, cloud types, extended weather, surface seasons:** Adds `PARTICLE_LAYER` (pollen/dust, fireflies, spores, snow, hail, embers, cosmic motes), `CLOUD_TYPES` (cumulus/stratus/cirrus/storm anvil), `WEATHER_EFFECTS` (sandstorms, blizzards, fog banks) and `SURFACE_SEASONS` (winter frost/snow, patchier autumn leaves, rain puddles, summer heat shimmer).

**1.4.0 — temporal stability update:** Adds configurable HDR TAA history with camera/depth/screen rejection and a 3×3 YCoCg neighborhood clamp; contact-hardening PCSS shadows; world-radius directional horizon AO; SSR adaptive stepping, thickness handling, hit confidence, and rough reflection resolve; Legacy Filmic, ACES-like, and AgX-like tone mapping; more restrained exposure and bloom; and TAA-aware volumetric jitter. Projection jitter remains disabled to protect hand rendering and Iris compatibility.


End rift core and ringed giant close-up:

![End planetary sky](previews/end-sky.png)

**1.3.0 — End planet visual upgrade:** The four End planets now have independent orbits and silhouettes: inner planets orbit faster, outer ones slower, and each has its own orbital distance and apparent size; the ringed giant's rings scale with its radius. Every planet gains a procedural atmospheric glow that peaks at the silhouette, falls off into a soft haze, and keeps only a narrow rim over the disk edge so surface colors stay intact. Glow color and strength vary by planet type (cold blue ocean world, volcanic orange, amber ringed giant, icy blue outer world), with stronger scattering on the side facing the central star. The full GPU compile matrix, all synthetic-scene render regressions, and the End-sky fixture checks were rerun and passed. In-game acceptance and FPS measurements are still pending.

**1.2.0 — performance update:** Overworld cloud shadows are now evaluated per vertex and interpolated, instead of recomputed per fragment with FBM; water fragments return early before the generic lighting pass, removing work that was previously overwritten; PCF shadow sampling drops to 4 taps beyond 60% of the shadow distance, in addition to the existing distance fade. These changes passed the full GPU compile matrix and all synthetic-scene render regressions. In-game acceptance and FPS measurements are still pending.

**1.1.0 — End planetary sky:** Four orbiting planets (including one ringed giant), a central star, and a fixed starfield were added to the End. Movement is driven by view direction and time, with configurable orbital/rotational speed. `END_PLANETS` and `END_ORBIT_SPEED` options were added under a new "End starfield" menu page (Chinese and English), enabled by default and limited to the End dimension. Six synthetic-scene checks passed (foreground occlusion, orbital motion, frozen at zero speed, clock reset consistency at 0.5/1/2× speed, static when disabled, no leakage to other dimensions); in-game acceptance is still pending.

**1.0.2 — buffer format fix:** Buffer-format metadata was moved into Iris-supported multiline comments, fixing `RGBA16F` / `RGBA8` / `R11F_G11F_B10F` being treated as undefined GLSL variables in `deferred.fsh`. The validator no longer injects format macros that the release does not contain. Iris is confirmed to allocate all 7 buffers as expected.

**1.0.1 — clear-color crash fix:** Fixed a load-time crash caused by Iris parsing single-argument `vec4` clear colors. The four clear colors now use four explicit components and pass parsing against real Iris 1.10.9 and 1.11.2 releases.

## Requirements

- Target game: Minecraft Java Edition **26.2**.
- Fabric with the **Iris 1.11.2 + 26.2 Fabric build** and **Sodium 0.9.1 for 26.2**.
- OpenGL 3.3 / GLSL 330 or newer compatibility profile, converted by Iris for the game's core pipeline.
- GPU verification device for this round: NVIDIA GeForce RTX 5080 Laptop GPU, driver 616.64, OpenGL 4.6.
- Minecraft 26.3, Vulkan, OptiFine, Distant Horizons, Voxy, and custom rendering mods are not claimed to be supported.

## Installation

1. Install Minecraft Java 26.2 with the matching Fabric, Iris, and Sodium builds (or use the [Iris installer](https://irisshaders.dev/download/) and select the game version).
2. Put **Galaxy Shader-1.15.24.zip** into that instance's `.minecraft/shaderpacks/` folder. Do not extract it.
3. Launch the Fabric instance and open `Options → Video Settings → Shader Packs`.
4. Select `Galaxy Shader-1.15.11.zip` and click `Apply`.
5. Open the shader settings and choose `HIGH` or `MEDIUM`. Menu labels are provided in both Chinese and English.

The source folder is also installable: copy the whole `Galaxy Shader` directory into `shaderpacks/` so the path resolves to `shaderpacks/Galaxy Shader/shaders/shaders.properties`. Inside the ZIP, files live directly under `shaders/` with no extra nesting.

## Features

| System | Implementation |
| --- | --- |
| Lighting | Dynamic sun/moon direction, warm sunrise/sunset tint, weather attenuation, hemispheric ambient light, minimum cave brightness, held-light approximation |
| Shadows | Stable-grid orthographic map, PCSS blocker search, contact-hardening variable penumbra, static sample rotation, far-distance sample reduction and fade |
| Sky | Rayleigh/Mie phase and optical-thickness approximation, sun/moon disks, stars, day-night gradient, Overworld galaxy band and nebulas, aurora, shooting stars, calendar-driven celestial events, anti-solar Earth shadow and Belt of Venus, zodiacal light, night zodiacal band and gegenschein, night airglow, 22° ice halos with parhelia and a sun pillar, a 46° ring and circumhorizontal arc, sunset green flash, anti-solar rays |
| End sky | Rift core (faceted crystal core, four diffraction streaks, bipolar plasma jets, two belts of shattered shards), one ringed giant and a fixed starfield; `END_PLANETS` / `END_ORBIT_SPEED`, End only |
| Clouds & weather | Ray-marched volumetric clouds (far samples drop fine noise detail, single-plane fallback on low), cumulus/stratus/cirrus/storm-anvil cloud types, noctilucent high cloud bands, winter nacreous clouds, sandstorms/blizzards/fog banks, rain streaks, post-rain rainbow, rainy-night moonbow, daily sky variation, smooth wetness accumulation, block splashes, real lightning illumination |
| Air particles | Daytime pollen and dust, night fireflies, forest spores, snow-biome snow, storm hail, Nether embers and End cosmic motes; selected by biome, season, weather and dimension |
| Water | Multi-frequency wave normals (up to three layers), multi-scale expanding/fading rain rings, wind/storm disturbance, storm highlights, Fresnel, analytic sky reflection (`WATER_REFLECTIONS` can add traced hits), one displaced refraction lookup plus one extra tap, Beer-Lambert absorption, shoreline foam, underwater caustics and blue-green volumetrics, deep-water fog |
| Reflections | SSR for wet or LabPBR smooth surfaces; adaptive stepping, thickness/refinement, hit confidence, inexpensive rough resolve, environment fallback |
| Vegetation | Grass, flowers, crops, leaves, vines; world-coordinate and gust-driven motion; matching animation for tall-plant halves and the shadow pass |
| AO / indirect | Directional GTAO-style horizon search with world radius and edge-aware weighting; separate short-range color transport |
| Materials | LabPBR normals, linear roughness, dielectric F0/metal, material AO, emissive read; vanilla parameters when no resource pack provides them |
| Emissives | Torch, lantern, soul fire, lava, redstone, sea lantern, end rod, campfire, lit furnace and other classified emissives; visible emissive surfaces project screen-space colored light onto geometry |
| Atmospheric fog | Depth-occluded height fog, lowland/valley fog, distance haze, and weather/humidity response, with biome temperature/rainfall shifting fog colour and density; warm volcanic fog in the Nether; dark nebula and void fog in the End |
| Volumetric light | Shadow-map ray marching, canopy-contrast shafts, dawn/dusk boost with midday suppression, cloud attenuation, and lightning scatter |
| Post-processing | Restrained HDR bloom, Legacy Filmic / ACES-like / Natural Filmic mapping, bounded exposure and natural white balance |
| Camera | Reprojected TAA history, rejection and YCoCg neighborhood clamp; optional light FXAA, depth of field and camera motion blur |

## Recommended settings and quality presets

Default is `HIGH`: 2048 shadow resolution, 128-block shadow distance, soft shadows, moderate reflections and bloom. Start at 1080p and a 16-chunk render distance, then adjust from the actual frame rate. The table below is a quality budget, not a performance guarantee.

| Preset | Shadow map / distance | Effect budget |
| --- | --- | --- |
| POTATO | 1024 / 64 | TAA/PCSS/SSR/AO/indirect/volumetrics/advanced weather/terrain fog off; four-tap PCF |
| LOW | 1024 / 96 | Low TAA, AO, rain ripples, and terrain fog; PCF; SSR/indirect/volumetrics off |
| MEDIUM | 2048 / 96 | Medium TAA/weather; low PCSS/GTAO/SSR/volumetrics/terrain fog |
| HIGH | 2048 / 128 | Default; high TAA/weather and medium PCSS/GTAO/SSR/volumetrics/terrain fog; 24-step clouds; water reflects the analytic sky |
| ULTRA | 4096 / 192 | Maximum weather/terrain fog and higher PCSS/GTAO/SSR/volumetric budgets; 36-step clouds; water adds traced hits |
| CINEMATIC | 8192 / 256 | 16+24 PCSS, maximum weather/atmosphere/screen-space budgets and screenshot DoF; water adds traced hits |

Lowering `SSR`, `Volumetric Light`, `Cloud quality`, and shadow resolution is usually the fastest way to cut cost. Keeping water reflections on "Sky only" is far cheaper than "Sky + screen space", so leave the default when chasing frame rate. A single 8192² 32-bit depth map is roughly 256 MiB before other Iris targets and caches. Do not use CINEMATIC as a daily setting.

## LabPBR resource packs

`LabPBR materials` defaults to **Auto**: extra material textures are sampled only when a resource pack declares LabPBR through `texture.properties`. Without a resource pack these textures are not sampled, avoiding wrong defaults causing abnormal highlights.

If you are sure a pack is LabPBR 1.3 but does not declare the format, choose **Force LabPBR**. Do not force it on ordinary resource packs. `_n` reads RG normals and AO from the B channel; `_s` reads smoothness from R, reflectance/metal from G, and emissive from A; an emissive alpha of 255 is correctly ignored. Parallax occlusion, displacement, and subsurface texture channels are not implemented.

## Known limitations

- In-game acceptance is still pending; GPU tests use synthetic block scenes and do not include Iris runtime shader translation, real chunk streaming, game UI, mod interoperability, or player input.
- SSR can only reflect **opaque** content already on screen; off-screen content uses an environment approximation. Water refraction is based on the opaque scene; refraction through multiple glass/water layers is not solved recursively.
- Water reflects the analytic sky by default (`WATER_REFLECTIONS` = Sky only), so on-screen trees, hills and buildings do not appear in the water. Choosing "Sky + screen space" adds those traced hits and costs noticeably more at the water pixels.
- A single shadow map is used rather than cascaded shadow maps; thin glass/water does not cast colored shadows. Far shadows fade to sky-lit occlusion; extreme terrain still needs real-game inspection.
- Indirect light and emissives are approximated. Vanilla lightmaps carry no source color; the new colored light comes from screen-space propagation of visible emissive surfaces and cannot reach off-screen or fully occluded sources, so it does not equal Photon's voxel flood-fill / colored GI.
- Overworld clouds are ray-marched along the view ray rather than a 3D voxel cloud field, and distant samples keep only the large billow shape. Flying above the cloud layer, world-coordinate resets, and long-distance travel still need real-game inspection.
- Minecraft/Iris directly exposes Clear, Rain, Thunder, and continuous `rainStrength` / `wetness`. The pack derives its Cloudy mood continuously from configured cloud cover, residual wetness, and light attenuation; it does not add a new game weather type. Surface splash exposure uses skylight and face orientation, so per-drop occlusion under complex overhangs remains approximate.
- TAA does not jitter the projection; moving entities have no dedicated motion vectors and rely on depth, luminance, and neighborhood rejection. Auto-exposure still uses Iris's smoothed eye light rather than a full-scene histogram.
- Terrain and block entities support material normals; ordinary entities and armor do not have full LabPBR reads. Named metals use matching F0 for direct specular highlights, with an Albedo-metal approximation for environment reflections.
- The HUD is not blurred by default; post-processing applies to the world view. The held item has its own mask, but GUI, third person, enchant glints, beacons, and special objects still require in-game acceptance.
- Emissive regions are approximated through material textures or block type/brightness thresholds; fine-grained emissive detail such as furnace sides is less precise than dedicated PBR emissive maps.

## Troubleshooting

- **Pack does not appear in the list:** verify it is in the current launcher instance's `shaderpacks/`, and that the ZIP has `shaders/` at its root.
- **Compile error or black screen:** first disable the shader pack to restore the image, then confirm the Iris/Sodium builds match 26.2. Keep the first shader error from `.minecraft/logs/latest.log`, plus your GPU model and preset, to help diagnose.
- **Too bright or odd reflections:** set `PBR_MODE` to Auto or Off, and check whether the resource pack really is LabPBR.
- **Low frame rate:** switch to MEDIUM/LOW, lower reflections, volumetric light and shadow distance, and disable DoF/motion blur.
- **Screenshot too dark/too bright:** adjust Exposure; disable Eye Adaptation if you need a fixed exposure.
- **Grey, overcast-looking morning or dusk:** start with `Dawn/dusk haze` (`DAWN_HAZE`) on the Atmosphere page. The default is 1; 0 gives a crisp clear sky and 2 restores a heavy fog bank. Then check that `Cloud coverage` is not set very high - coverage now only adds clouds instead of dimming the sunlight and sky with them.
- **Missing off-screen reflections:** that is the screen-space reflection range limit; the pack already includes an environment fallback.

## License / credits

The shader source and documentation are original and released under the [MIT License](Galaxy Shader/LICENSE). No GLSL or textures from other shader packs were copied. The release ZIP does not contain Minecraft, Iris, Sodium, or third-party assets.

Interface references: [Iris docs](https://shaders.properties/current/) and the [LabPBR standard](https://shaderlabs.org/wiki/LabPBR_Material_Standard). Lighting uses public mathematical models such as Fresnel, GGX, Rayleigh/Mie, and Beer–Lambert. The filmic curve is a common ACES fit, not full ACES color management.

Project structure and validation workflow: [ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md) · release history: [CHANGELOG.md](Galaxy Shader/CHANGELOG.md) · validation records: [VALIDATION.md](Galaxy Shader/VALIDATION.md)
