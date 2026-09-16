# Reusable parts and visual assembly

Design the part first, then place it in models. The visual workflow does not
rebuild a regiment when one crest, helmet, torso, shield or weapon changes.

Follow the [army design requirements](design-requirements.md) for printer,
feature-size and support targets while creating or combining pieces.

The library stores independently versioned parameter definitions in
`fdm_sculpt/components/parts/`. These define primitives, transforms, bevels,
ordered local Exact operations and named landmarks, including a local `mount`.
They do not import Blender or derive their geometry at runtime from a complete
spearman. The one-time extraction script preserves the revision-11 design;
tests reconstruct every original primitive transform and operation order.

`specs/elf-modular-visual.json` places these parts to recreate the five current
spearmen. A part reference includes its integer revision and definition hash.
Multiple placements share the same generated asset. The assembly contract is
not restricted to five figures, spearmen or one type of army unit.

## Routine iteration

```powershell
py -3.13 -m fdm_sculpt.atelier list
py -3.13 -m fdm_sculpt.atelier part aurelian.crest@2 --seed 1001 --output out/crest-review
py -3.13 -m fdm_sculpt.atelier compose specs/elf-modular-visual.json --seed 1001 --output out/army-review
py -3.13 -m fdm_sculpt.atelier plan specs/elf-modular-visual.json --seed 1001
```

`part` previews a piece alone, centered in the viewport. `compose` creates the
assembled scene. `plan` reports which parts need compilation without starting
Blender. All commands preserve earlier output directories. `--render` requests
one optional image; the default writes only the orbitable scene and records.

The current composition includes curved breastplates, rounded tunic shoulders,
chainmail skirts, broader shields with thicker seahorses, fitted helmet crests,
and organic faces with an integrated brow and mouth groove. Earlier part
revisions and the original modular assembly remain pinned for comparison.
The [spearman underside study](spearman-overhang-study.md) adds permanent
tapers beneath the neck, hems, grips, sleeves, shield details and spearheads,
with separate CLI slice comparisons and preserved earlier revisions.

On Windows, `scripts/open-review.ps1 -Scene out/army-review/assembly.blend`
loads a saved review into the existing Blender window, or starts Blender if
none is running. This desktop helper requires an interactive desktop and uses
the Python console under the pointer; it confirms the loaded path in the title.

For a shape change, add a new revision file for the affected part, update its
golden hash and repin the intended placements. Keep earlier definitions. A new
crest used by five figures is compiled once. Unchanged parts reuse their caches.
Changing only placement, rotation or assembly seed compiles no part geometry.
The seed remains explicit; these particular recipes contain no random geometry.

Cached assets live in ignored `out/part-cache/` directories keyed by the part
definition, Blender version and compiler implementation. Each contains the
local procedural source, evaluated preview collection, landmarks and a hashed
manifest. The visual collections are marked as Blender assets. Cached files
are immutable: older saved assemblies continue to refer to their pinned parts.
Do not delete caches referenced by a saved scene. These local working scenes
link their cached assets; they are not yet portable release packages.

An assembly uses lightweight collection instances. It retains hidden source
instances in `SOURCE_PRIMITIVES`, visible instances in `VISUAL_PREVIEW`, and an
empty `EVALUATED_EXPORT`. The saved scene is reopened to check definitions,
local Exact operands, cached mesh hashes and placement transforms. No full
solid union, mesh printability audit, repeat geometry build or slicer runs.

## Reusable models and unit variants

The first command model is a standard bearer with a leaf-tipped pole,
crossbar, broad banner, eight-point star relief and a curved war horn. The pole and cloth are
independent revisioned parts. The bearer reuses the existing gripping arm,
armor, head and crest; the solo review adds a 4 × 5 mm ground
base. The center-unit layout replaces only the third spearman's equipment.
Standard revision 2 centers the cloth on a symmetrical crossbar, widens the
top to 5.2 mm and tapers the lower edge to 3.1 mm. The cloth hangs in front of
the shaft so the pole does not interrupt the seahorse.
Revision 3 replaces the two hanging tips with a single point rooted in the
shaft. The cloth expands gradually in width and depth, the crossbar rests
on the cloth, and the seahorse is embedded to about 0.25 mm of relief. This
targets an upright print without removable supports; sliced support validation
remains part of release preparation. The reusable `aurelian.war-horn@6` replaces
the bearer's shield and its attachment pieces while keeping the existing hand.
The horn has a smooth sweeping curve, gradual flare and rounded lip, retaining
the reviewed grip and mouthpiece centers. Banner revision 4 expands the design to a
7 mm-wide, nearly rectangular field with a 6.6 mm lower hem and a 5.4 mm field
height. Its tapered lower attachment still grows from the pole beneath the
field; the taller shaft keeps the enlarged cloth clear of the helmets.
Banner revision 5 retains that outline and adds a continuous rounded lining
with an even inset and a flat emblem field. The separate reusable
`aurelian.standard-insignia@1` is a centered eight-point elven star with
0.25 mm attached relief. Shields retain their seahorses. Both bearer layouts
mount the star at the center of the banner field through the shared recipe.
Banner revision 6 extends this lining around the full tapered lower perimeter,
replacing the horizontal divider with a continuous border that follows the
root's depth ramp. The cloth shape and star placement are retained.
Banner revision 7 makes the entire silhouette one flat tapestry. The lower
section shares the upper face's depth, removing the transverse seams and
letting the perimeter lining continue in one plane. The narrow root overlaps
the pole at its back; this changed attachment still awaits sliced validation.
Banner revision 8 centers the star vertically across the full banner height
and restores a 1.18 mm depth taper at the bottom tip. The lining remains flat
and closes straight across above this short ramp. The support-free design
target still requires sliced validation during release preparation.
Revision 9 joins each lining stroke directly to the tapestry so the Exact
union retains the complete cloth solid after the root cut.

The shared `aurelian.spear@2` lengthens each ordinary spear shaft by 25 percent,
from 11 to 13.75 mm. Its foot, grip alignment and diameter stay fixed; the
existing leaf tip moves upward 2.75 mm. Revision 3 retains that geometry and
adds a rounded collar with a tapered underside below the leaf. The current
spearman layouts use revision 4, which lengthens the lower ramps and matches
the depth of the two blade sections without changing the shaft or terminal tip.

The current helmet is `aurelian.helmet@7`: its lower nape blends into the crown.
It preserves revision 5's inset cap base and upper shell. The
[current design notes](helmet-flush-nape.md) also record the outward left-arm
placement, ground-contact cape hems and removal of the shield feet.
The shared bearer recipe uses banner revision 10 with a raised insignia mount
and `aurelian.horn-arm@6`, keeping the grip forward to keep the horn clear of
the chest plate and mail skirt. The horn is carried upright with its bell facing
outward and upward; its lower stem is seated in the hand so it grows from the
hand instead of starting as a hanging island. Revision 4 raises the elbow and
brings the hand closer to the shoulder, shortening both arm segments by about
40 percent while retaining a rising forearm. Revision 5 enlarges the palm,
grouped fingers and thumb by 30 percent without changing the pose; revision 6
enlarges them another 30 percent, reaching 1.69 times the original dimensions.
This is a support-free design
intent, pending sliced validation. These remain visual-only revisions.

```powershell
py -3.13 -m fdm_sculpt.atelier compose specs/elf-standard-bearer.json --seed 1001 --output out/bearer-review
py -3.13 -m fdm_sculpt.atelier compose specs/elf-unit-center-standard.json --seed 1001 --output out/center-standard-review
py -3.13 -m fdm_sculpt.atelier part aurelian.standard-banner@10 --seed 1001 --output out/banner-review
py -3.13 -m fdm_sculpt.atelier part aurelian.standard-insignia@1 --seed 1001 --output out/insignia-review
```

`specs/models/elf-standard-bearer.json` is the shared model recipe for both
layouts. Its `source` selects a reviewed figure from another assembly.
`origin_mm` sets the model's local origin. `remove` names unwanted slots;
`parts` adds or replaces slots with pinned component references, definition
hashes and local transforms. Body revisions inherited from the source and
equipment revisions in this recipe are therefore shared by both layouts
when they are next composed. Previously saved reviews retain their snapshots.

The archer recipe `specs/models/elf-archer.json` reuses the reviewed head,
helmet, crest and boots. Body and feet turn 90 degrees to the firing direction;
the head remains aimed forward. Separate tunic, bow arm, drawing arm, longbow,
arrow and quiver components replace the heavy spearman equipment. The current
tunic has a wider flared skirt and shallow cloth creases; both fists use broad
beveled knuckles and distinct rounded thumbs. The bow's lower tip meets the
tunic, and the arrow spans the drawing hand and bow grip. These are visual
design choices, pending manufacturing and sliced validation.

```powershell
py -3.13 -m fdm_sculpt.atelier compose specs/elf-archer.json --seed 1001 --output out/archer-review
py -3.13 -m fdm_sculpt.atelier compose specs/elf-unit-archers.json --seed 1001 --output out/archer-unit-review
py -3.13 -m fdm_sculpt.atelier part aurelian.archer-tunic@3 --seed 1001 --output out/archer-tunic-review
```

### Ten archer poses

`specs/elf-archer-variants.json` displays ten reusable model recipes on separate
bases in two rows. The viewer calls this **Archer variants (10)**; isolate a
pose with the Figure selector. Recipe filenames and pose metadata live in
`specs/archer-variants-index.json`.

| Variant | Pose |
| --- | --- |
| 01 | Aiming forward, arrow nocked |
| 02 | Aiming left, bow canted |
| 03 | Aiming right, bow canted |
| 04 | Empty bow at the ready |
| 05 | Empty bow, turned stance |
| 06 | Reaching into the quiver |
| 07 | Pulling an arrow from the quiver |
| 08 | Shortblade held at the side |
| 09 | Shortblade raised |
| 10 | Hand withdrawn after release |

All bows share `aurelian.archer-bow-ferrule@1`, a metal-styled socket with
leaf plates and raised bosses. Empty bows use the straight-string revision;
the aiming poses retain the drawn string. Quiver-reaching poses use an outward
quiver and matching arms that clear the head and helmet. These remain visual
reviews, not sliced or physically tested print files.

Model recipes can apply a rigid `transform` to the whole figure and a
`transforms` map to individual slots. Slot transforms are applied in model
coordinates after part overrides, then the whole-model transform is applied.
This lets variants inherit new shared part revisions without copying their
definitions or rebuilding geometry when only angles change.

```powershell
py -3.13 -m fdm_sculpt.atelier compose specs/elf-archer-variants.json --seed 1001 --output out/archer-variants-review
```

A unit layout can inherit a `base_assembly` and place `models`. Each model
instance has a name, a recipe path and a rigid `mount`. Set `replace: true`
to replace an existing figure with that name. New layouts can instead list
base `placements` and any number of model instances. All paths are relative
to the file containing them. Misspelled replacement names, duplicate slots,
stale component hashes and recipe cycles are rejected before Blender starts.

`atelier plan` expands these recipes without generating geometry. Composition
saves the fully resolved placements and checked part provenance. Repositioning
or combining cached models compiles zero geometry. Editing one banner revision
compiles that banner once, and every model using it shares the cached mesh.

The viewer's **Model / unit** selector switches between published layouts
without running a build. **Latest update** follows whatever was just composed;
selecting a named layout follows updates to that layout. Meshes shared by
recently viewed layouts stay cached in the browser. Use Ctrl-hover to identify
the **Standard pole**, **Banner**, and **Banner insignia** separately.

## Later publication or release

Spearmen and their standard bearer share `aurelian.cloth-waist-wrap@1` in
the `waist-wrap` slot. Its soft oval band and three horizontal cloth folds
cover the plate/chainmail seam. The wrap uses the plate mount; archer recipes
omit it because they wear a continuous tunic.

Arrow support revisions 1–3 are preserved for later reuse but removed from
current archer recipes at the user's request. Broader support-free modeling
changes are deferred until the user supplies their intended policy.

Archers now share tunic revision 4 (18 percent wider hem), bow fitting
revision 3 (larger gems and curved diamond plates, recessed at the fist), and leg revision 4
(boot uppers aligned with the soles). Variants 5 and 7 lower their bows by
1.0 and 1.65 mm with matching reusable arm poses. The standalone
`specs/elf-archer-sergeant.json` holds an undrawn bow at the side and places
the shared horn mouthpiece at the face's mouth landmark.

Bow revisions 4 (drawn) and 5 (undrawn) use the reusable
`components/bow_grips.py` recipe with fitting revision 3. An ordered Exact
annular subtraction keeps a 0.8 mm handle within the fist over a 1.8 mm
grip length. The limbs, string, grip landmarks and poses retain their reviewed
positions. `tests/bow_grip_scene_probe.py` checks the evaluated handle against
the posed palm in every archer layout; this is visual geometry verification.

Keep working models visual-only until release work is requested. Release
preparation must materialize the selected modular composition, package its
dependencies, and perform the applicable export/print checks. The historical
`regiment build` commands still build their pinned whole-spearman recipes;
they do not automatically include newer modular part revisions. Do not use
those old recipes to release a subsequently changed modular model.

For a requested physical trial of a saved modular review, use:

```powershell
py -3.13 -m scripts.generate-spearman-print-trial
py -3.13 -m fdm_sculpt.atelier compose specs/elf-spearmen-print-trial.json --seed 1001 --output out/spearmen-print-source
py -3.13 -m fdm_sculpt.modular_print out/spearmen-print-source --seed 1001 --output out/spearmen-trial --figure-cache out/original-spearman-cache-04
```

This verifies the saved component provenance, materializes shared parts with
Exact unions, joins the placed figures and base, packs scene dependencies,
and exports a single-material STL and 3MF. It then prepares and reopens a
Prusa XL project with the preserved tool-2 profile, slices it, and records
contour, deposited-support, face-landmark and automatic-support diagnostics.
`--no-slice` stops after geometry export for an independent comparison build.
The output is explicitly an unvalidated manufacturing trial. Check the
reports before attempting a print; successful export does not establish
structural dimensions, support-free printability or physical performance.
`regiment assess <trial> --support-audit` also accepts these modular trials.

The trial retains the original reviewed skirt @3 and its chainmail exactly,
as requested. Coarser skirt @4 and @5 experiments are preserved in the recipe
history but are not used by the trial. The checked original-mail figure cache
is used explicitly for this prototype; cache preparation requires the saved
original-mail repair and part checkpoints. It is not a general release builder.
Internal fill @1 adds 180 primitive boxes inside sealed microscopic pockets.
The original skirt @3 is unchanged. The filler-box containment probe finds no
exterior intersections, and the repaired exterior passes a bidirectional
surface comparison at 0.000002 mm, using double-precision triangle distances
where float BVH measurements become unstable on thin planar triangles.
The internal filler also passes independent cached-mesh hash comparison and
saved-scene provenance. Equipment joins @3 increases the spear brace diameter
from 0.80 to 0.81 mm to investigate a degenerate triangle at its shaft contact;
its endpoints, bevel and assembly placement stay unchanged. This adjustment
is confined to the print-trial specification.
Spearman join fill @1 adds three further contained primitive boxes to seal
microscopic pockets produced where that first figure meets the original mail.
The isolated filled figure passes artifact topology and self-intersection
checks; stand fusion and slicing remain separate required checks.
The trial places complete figures 0.01 mm higher, except the fourth at
0.005 mm, to avoid numerical cape/soil crossings. These seating offsets apply
once to every part of each figure; geometry and equipment alignment remain
unchanged. Cached placement validation permits those rigid translations and
rejects individual part movement. Native Exact fusion with a 0.0000005 mm
numerical weld passes the full stand's topology and intersection checks in
the seating study. `out/spearmen-original-print-03` and its independent repeat
produce byte-identical STLs, with no removed faces and passing packed-scene
provenance. The Prusa project reopens and slices using embedded XL tool-2
settings. Pocket, shaft and boot-contact probes pass. The sliced support,
contour and brow-landmark screens fail, so the result remains an experimental
trial, not a digitally validated support-free print. The automatic-support
slice is diagnostic only. See the output's `PRINT-TRIAL.md` and `previews/`.
Trial trim @7 moves its cape cutout rearward by 0.04 mm, providing a real
overlap at the seam instead of coincident surfaces. The trial trim placements
rise 0.03 mm to separate coincident lower hem surfaces. The original army's
visual specifications retain their reviewed revisions. Definitions and golden
hashes also preserve the intermediate trial skirt @4.

The first trial uses five copies of the first spearman, 4 mm apart. Other
reviewed poses remain in the visual army: the second pose exposed an enclosed
cavity at its spear join during manufacturing checks. The trial may reuse a
previously checked first figure and base with `--figure-cache <prior-build>`;
that path verifies the complete placement contract, records the source scene
hash, rechecks both cached solids, and performs a fresh Exact stand union.

## Terrain and bases

See [terrain and magnet bases](terrain-bases.md) for Blender-free generation,
seeded surface presets, boot clearance and the current 2 mm army bases.

## Spearman variants and hunting hawk

`specs/elf-spearman-variants.json` contains ten visual variants: six spear
poses, three short-sword poses and a sergeant carrying a hunting hawk and
short sword. `specs/spearman-variants-index.json` names each reusable model.
The sergeant also has a standalone review in
`specs/elf-spearman-hawk-sergeant.json`.

Generate the pinned definitions without Blender using
`py -3.13 scripts/generate-spearman-variants.py --seed 1001`.
The generator preserves existing recipes and refuses conflicting overwrites.
`fdm_sculpt/components/spearmen.py` owns three sword arms, the falconry-glove
arm and the perched hawk with folded wings, layered feathers and hooked beak.
The models reuse the approved helmets, faces, armour, boots and short blade.
Each model normalizes the inherited 1 mm height offset before the gallery
adds it once; body and soil use the current magnet-ready solo bases.

Compose through `atelier compose specs/elf-spearman-variants.json --seed 1001
--output out/<fresh-review>`. Earlier reviews remain available on disk.
Archer sergeant horn-arm revision 2 uses `components/hand_grips.py` to rotate
the fist along the horn's local tangent while retaining shoulder, elbow,
grip and mouthpiece positions. These remain visual-only reviews.

Spearman variants now face predominantly forward: inherited head yaw is
normalized before applying glances of at most 6 degrees and body turns of
at most 5 degrees. Stances, arms and modest spear inclinations provide the
main variation. Shared shortblade revision 2 has a 3.57 mm straight blade
with a short tapered point, a 1.9 mm hilt, a wider crossguard and a visible
pommel. Its grip origin is unchanged across spearmen and archers.

Both sergeants wear `aurelian.sergeant-helmet@1`: the approved revision 5
crown with paired swept feather wings and a brow jewel. The shared recipe
in `components/sergeant_helmets.py` preserves the crown, face opening,
mount and cap, and adds the ornaments with ordered Exact unions. Ordinary
troops retain the plain helmet. Helmet, head and crest move together.

Sergeant helmet revision 2 enlarges the feathers by 50 percent in length
and 25 percent in width, with a more upright sweep and fixed attachment
points. The crown, face opening and brow jewel retain their earlier shape.

`components/garment_trims.py` owns the separate tunic and mail-skirt trim
recipes. Revision 2 adds a 0.68 mm front band and 0.5 mm hem band, with
recessed creases down the front and around the bottom. The edging overlaps
the reviewed garment and keeps its crease outside the existing chain links.
`tunic-trim` and `skirt-trim` slots share their garment's mount and pose;
cloth figures remove inherited mail trim along with the mail skirt.

Mail-skirt trim revision 4 stops at the waist wrap's lower edge (local
Z = -1.25 mm) and ends the hem edging ahead of the cape-covered rear
(local Y = -0.5 mm). Both limits are local Exact intersections. The front
crease and hem height are retained; the evaluated trim clears all five
reviewed cape variants. This revision remains available as a saved review.

Mail-skirt trim revision 6 replaces the straight rear cutoff with Exact
subtraction of the matching cape's pinned primitives. Five fitted trims
follow the five cape shapes and meet their surfaces at both sides; the
waist-wrap stop remains unchanged. A rear limit at local Y = 0.5 mm removes
the unwanted band behind the cape while retaining contact on both sides.
Cape definition hashes are recorded in
the trim recipes. Archers now use their tunic's existing edging without
the separate tunic-trim overlay.

Archer variants 11–13 aim upward at 20, 30 and 40 degrees for rear ranks.
`scripts/generate-elevated-archers.py` creates pinned arm definitions and
model placements without Blender. The shoulder anchors stay fixed while
the bow, ferrule, arrow and hands share a rotation around the nock. Head,
helmet and crest tilt together; legs, tunic and quiver retain their poses.
The main archer gallery now has 13 variants, with a separate three-model
review in `specs/elf-archer-rear-ranks.json`. These remain visual-only.

`specs/elf-swordmaster.json` reviews a two-handed swordmaster on the solo
soil and magnet base. `components/swordmasters.py` owns a long diamond-section
greatsword with a wrapped two-hand hilt, swept guard and pommel, plus two
arms with broader pauldrons. The hands share the sword's grip axis and its
upper/lower grip landmarks. `scripts/generate-swordmaster.py` writes the
pinned model, preserving the infantry's face, helmet, cape, mail trim and
stance while removing the shield and spear. Visual-only; no print validation.

The armored swordmaster adds a heavier ridged cuirass, layered swept
pauldrons, jeweled waist plates and a crown-mounted hair braid. These are
independent recipes in `components/swordmaster_armour.py`, pinned by
`scripts/armour-swordmaster.py`. Braid revision 2 uses rounded interwoven
locks. The cloth waist wrap and original crest are replaced; the helmet
outline, face and two-handed sword pose remain intact.

The current swordmaster replaces the braid with a fuller flowing helmet
plume that drapes close to the helmet's rear. Pauldron revision 2 uses
broad beveled metal caps, raised border panels and overlapping lower
plates instead of the earlier feather-like sweep. Both are independently
cached; the sword pose and other armor retain their geometry.

Helmet plume revision 2 replaces the segmented locks with one smooth
hair envelope and shallow engraved strand lines. It remains attached at
the crown and drapes down the helmet's back; all other pieces are reused.

Plume revision 3 customizes the silhouette with an asymmetric swept crown,
a tapered sideways fall, and seven finer curved grooves with staggered
ends. The crown attachment and helmet placement are retained. Its isolated
part review can be composed with `atelier part` before the assembled review.

`specs/elf-swordmaster-variants.json` presents ten two-handed guards, from
upright and high guards to wide parries, low guard, recovery and a forward
point. `scripts/generate-swordmaster-variants.py` pins the poses and paired
arm recipes from `components/swordmaster_variants.py`. Shoulder anchors
stay fixed, both hands follow the hilt, and whole-figure turns stay within
four degrees. Armor, hair, legs, cape and sword reuse the approved caches.

`specs/elf-swordmaster-sergeant.json` presents the officer in the upright
two-handed guard with the shared enlarged sergeant helmet and swordmaster
hair plume. `scripts/generate-swordmaster-sergeant.py` normalizes the gallery
origin and pins that helmet change; all geometry comes from existing caches.

The swordmaster sergeant now wears a dedicated forged helmet with angular
temple plates, a reinforced brow and a metal rank badge. His waist armor
has a larger central plate, layered side panels, double chevron relief and
engraved detail. `components/swordmaster_helmets.py` owns these officer parts;
the hair plume and two-handed pose retain their reviewed placements.

Officer helmet revision 2 seats an oval gem above the brow in a crown-backed
setting. Both swordmaster waist variants now use revision 2: side plates
turn 38 degrees around the skirt, follow its flare by 8 degrees and have
reduced depth so they sit embedded in the chainmail. All ten poses inherit
the shared fit; the sergeant retains his larger central decoration.

Waist revision 3 enlarges the fitted side plates by 25 percent in width
and 22 percent in length, retaining their recessed depth and skirt angles.

The unit is now named **Bertmasters**. Viewer labels and new review labels
use Bertmaster, Bertmaster variants (10), and Bertmaster sergeant. Existing
component IDs, filenames and saved provenance retain `swordmaster` for
compatibility with reviewed geometry and caches.

`specs/elf-dragon-prince.json` introduces mounted Dragon Prince cavalry.
`components/dragon_princes.py` owns the horse, scaled barding, saddle,
riding legs, arms, reins, lance, dragon shield and horned helmet. The rider
reuses the approved head and heavy torso armor. A 6 × 12 × 2 mm soil base
has one centered 3 × 1 mm magnet recess. `scripts/generate-dragon-prince.py`
pins the recipes without Blender; barding revision 2 narrows the horse's
face plate to expose its ears and eyes. This is a visual prototype only.

## Dragon Prince reference pass

The cavalry now uses the [official Old World Dragon Princes image](https://assets.warhammer-community.com/preorders-apr19-tow_03-dragonprinces-hiahpptwh9.jpg)
from [Warhammer Community's April 2025 announcement](https://www.warhammer-community.com/en-gb/articles/gslgtn17/saturday-pre-orders-the-next-wave-of-high-elves-land/)
as a visual reference. Original primitive recipes in `dragon_prince_reference.py`
provide tall solid helmet wings, swept shoulder membranes, layered draped barding,
horse cheek fins, a flowing mane and a broad lance pennant. They replace the
prototype's plain horns and checkerboard scales. Horse @2, barding @3, helmet @2,
lance @2 and winged pauldrons @1 retain the existing assembly mounts and grip
landmarks. Earlier definitions and saved scenes remain available.

Generate with `py -3.13 -m scripts.generate-dragon-prince`, then compose
`specs/elf-dragon-prince.json` with seed 1001 into a fresh output directory.
The reference review is `out/elf-dragon-prince-reference-v2`. It is visual-only;
five changed parts compile while twelve unchanged parts reuse cached geometry.

The subsequent connected-head review (`out/elf-dragon-prince-connected-heads-v2`)
pins horse @3, barding @5, helmet @3 and reins @2. The horse skull is taller,
with raised eyes, ears and muzzle and an overlapping upper neck. Both helmets
use broad embedded roots and backward-swept overlapping plates. The reins follow
the raised bit while retaining the rider's grip. All assembly mounts remain
unchanged; thirteen components reuse their existing geometry. Barding @4 was an
unpublished failed prototype; @5 uses the supported frame transform. Visual-only.

The continuous-scale helmet review (`out/elf-dragon-prince-scale-helmets-v1`)
pins rider helmet @4 and horse barding @6. Two large overlapping solid scales
per side replace the pointed fins and rounded attachment pads. Broad roots,
planar ridges and blunt tapered ends create continuous backward-swept metal
surfaces. Only these two components rebuild; all fifteen other cached parts
and every assembly mount remain unchanged. Golden definitions are stored in
`dragon-prince-scale-helmets-golden.json`. This remains a visual-only review.

The upright-scale review (`out/elf-dragon-prince-upright-helmets-v1`) pins
rider helmet @5 and barding @7. The rider helmet is a new independent eight-sided
crown with cheek guards, an angular brow and an Exact-cut face opening. Both
helmets carry tall continuous plates with three rows of large diamond scale
relief. The prior head, pose and equipment mounts are preserved. Two revised
components compile and fifteen cached parts are reused; the corresponding
goldens are in `dragon-prince-upright-helmets-golden.json`. Visual-only.

Rider helmet @6 replaces the straight brow bar with two joined visor plates
that rise and recede toward the temples. The eye opening and other helmet
details are retained. Review: `out/elf-dragon-prince-visor-v1`; golden:
`dragon-prince-visor-golden.json`. Only the helmet recompiles; sixteen cached
parts and all placement transforms are reused. Visual-only.

`out/elf-dragon-prince-scalp-shield-legs-v1` combines shield @2 (35% wider,
30% taller, turned 40 degrees outward about its unchanged grip), horse @4
(revised forelegs and distinct hind stifle/hock/cannon segments, with unchanged
hoof locations), and barding @8 (a fitted scalp dome and metal ridge). Other
placements remain unchanged. The three new recipes have separate golden
fixtures and saved-scene provenance checks. This is a visual-only review.

Shield @3 enlarges the plate and emblem another 25% in width and height, retaining
the thickness, grip and outward-facing placement. Review:
`out/elf-dragon-prince-great-shield-v1`. Only the shield recompiles; sixteen
parts reuse their geometry. Golden: `dragon-prince-great-shield-golden.json`.

`out/elf-dragon-prince-gem-shield-reins-v1` pins shield @4 and reins @3.
The shield retains its large symmetrical plate and replaces the dragon emblem
with a centered oval gem and setting. The reins follow the lower cheek, pass
behind the shield and return to the original grip. `check-dragon-prince-reins.py`
runs in the saved Blender scene, probes at 0.02 mm intervals against cached
meshes with the rein radius included, and records `reins-clearance.json`.
Only localized bridle and fist contacts are exempt. The final review clears
the shield by at least 0.144 mm and other unrelated surfaces by at least
0.049 mm in that probe. These are visual clearances, not print validation.
Separate golden fixtures cover both new revisions; all assembly mounts remain
unchanged. Previous definitions and scenes are preserved.

Shield @6 adds a dense symmetrical field of shallow, flat-faced scales around
the exposed central gem. The sparse @5 study remains preserved. Review:
`out/elf-dragon-prince-scaled-shield-v2`; golden recipes cover both revisions.
Only the shield rebuilds; grip, placement and rein clearance are preserved.
Saved-scene provenance and the rein clearance probe pass. Visual-only.

Lance @3 replaces the thin horizontal pennant with a shaft-backed seal tab,
1.0 x 0.85 mm in section, with a tapered lower join and attached seal boss.
The main tab retains at least 0.76 mm after its bevel allowance; the 1.0 mm
shaft and grip are preserved. Review: `out/elf-dragon-prince-supported-seal-v1`.
Only the lance recompiles. This improves the design for FDM but is not sliced
or physically validated; it remains a visual-only review.

`out/elf-dragon-prince-tapestry-fitted-v1` combines three subsequent changes:
reins @6 follow the cheek/neck ellipsoid surfaces as shallow attached relief,
with local offsets over the bridle and neck plate; pauldrons @2 replace oval
caps with sharply sloping flat metal; lance @4 carries a longer downward
tapestry with three broad folds, a seal boss and hem. The tapestry is backed
by the shaft along its length, retaining a nominal 0.86 mm section and at least
0.75 mm after bevel allowance. All mounts, the rider grip and other cached
parts are preserved. Golden fixtures cover the intermediate rein revisions.
The saved-scene clearance probe allows the intentional shallow cheek/armor
contacts and still rejects intersections with equipment. It passes with the
updated review. This remains visual-only, pending slicing and physical trials.

`out/elf-dragon-prince-plain-lance-v1` restores plain lance @1, removing the
tapestry and seal. All seventeen components reuse existing geometry; the
lance grip, angle, and other assembly placements remain unchanged.

Horse @5 is the heroic-proportion study in `out/elf-dragon-prince-heroic-steed-v1`.
Visual references are GW's [Mounted Yeomen](https://assets.warhammer-community.com/articles/2316f34e-ad93-436e-b569-c5d47048cca1/cmbx2kbt3mukp5lt.jpg)
and [Dragon Princes](https://assets.warhammer-community.com/preorders-apr19-tow_03-dragonprinces-hiahpptwh9.jpg).
Lower leg diameter grows from 0.62 to 0.86 mm; upper limbs gain muscle forms,
joints grow 22%, shoulders/haunches fill out, and rounded broad hooves replace
the small rectangular feet. Joint centers, hoof X/Y locations, ground height,
saddle landmarks and all assembly mounts remain unchanged. The plain lance
is retained. Only the horse recompiles; recipe/golden, resolver, saved-scene
provenance, rein-fit and viewer checks cover the update. Visual-only.
