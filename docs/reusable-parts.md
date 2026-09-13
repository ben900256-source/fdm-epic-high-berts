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
adds a rounded collar with a tapered underside below the leaf. Both spearman
layouts use revision 3.

The current helmet is `aurelian.helmet@5`: its cap base is inset into the crown
to remove the exposed join, with finer primitive resolution on the curved shell.
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
