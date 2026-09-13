# Reusable terrain and magnet bases

Current army reviews use separate `base-body` and `terrain-surface` components.
They are visual-only. Magnet allowances are provisional until a physical trial;
no fusion, slicing or print validation has been performed.

The original procedural recipes live in `fdm_sculpt/components/terrain.py`.
`specs/terrain-presets.json` records all initial arguments, including seed 1001.
Pinned definitions live in `fdm_sculpt/components/parts/`; existing revisions
cannot be overwritten with changed geometry. Use a new positive integer revision.
Current bodies are revision 1. The original heightfield surfaces are revision 3,
with the enlarged archer soil revisions described below. At the user's request,
revision 3 completely replaces the earlier rounded-solid terrain with continuous
procedural heightfields, using the same class of technique as
[BaseForge](https://ms3dstudio.de/tools/baseforge/). This is an original
implementation of seeded layered noise and warped waves; no code, meshes or
heightmaps are imported from BaseForge. Earlier definitions and reviews remain
preserved, but no current army or gallery layout uses their terrain geometry.

Generate a definition without starting Blender:

```powershell
py -3.13 -m fdm_sculpt.components.terrain surface aurelian.my-soil --revision 1 --width 4 --length 5 --style soil --feature-scale 1 --relief-height 0.25 --density 1 --seed 1001 --output fdm_sculpt/components/parts
py -3.13 -m fdm_sculpt.components.terrain body aurelian.my-base --revision 1 --width 20 --length 5 --thickness 2 --magnet 3x1 --centers '[[-6,0],[6,0]]' --seed 1001 --output fdm_sculpt/components/parts
py -3.13 -m fdm_sculpt.atelier part aurelian.my-soil@1 --seed 1001 --output out/my-soil-review-1
py -3.13 -m fdm_sculpt.atelier compose specs/terrain-gallery.json --seed 1001 --output out/my-base-gallery-1
```

The body is local Z = 0..2 mm. Mount the terrain at Z = 2 mm; its continuous
substrate overlaps the body by 0.15 mm. Terrain settings do not include magnet
settings or body thickness, so changing those does not invalidate the surface.
Body definitions do not depend on terrain seeds. Figure cache keys depend on
neither. Assembly output directories must be fresh; rendering remains opt-in.

Styles are `soil` (continuous layered noise), `sand` (warped directional ripples),
`rocky` (ridged noise) and `meadow` (clustered grass-like streaks over low ground).
`components/heightfield.py` computes a seeded scalar surface and pinned samples.
The samples form a regular triangulated top with a flat bottom and closed sides,
all confined to the base footprint. There are no overlapping rounded texture
operands. This terrain-specific procedural mesh extension is authorized in
`AGENTS.md`; figure and base-body construction remains primitive/Exact CSG.

`atelier_heightfield_blender.py` is an opt-in adapter for these surfaces. Its
code hash affects only heightfield cache keys. The original primitive worker
and all cached figure and body geometry remain unchanged. Saved-scene checks
also compare the source vertices and faces against the pinned samples.

Solo bodies retain 4 × 5 mm footprints and have one centered 2 × 1 mm magnet
pocket. Strips retain 20 × 5 mm footprints and have two 3 × 1 mm pockets at
X = −6 and +6 mm. The bottom-open cylindrical recesses have 0.2 mm total
diameter allowance and 0.1 mm depth allowance, leaving 0.9 mm roof stock.
The recipe rejects roof, side or inter-pocket stock below 0.75 mm. `none`
generates a solid body. A 3 mm magnet is rejected on the 4 mm solo width.

`boot_regions(placements, definitions, base_mount)` projects each placed sole
primitive into base coordinates, with a 0.12 mm margin. It does not inspect
equipment. Pass those rectangles through `boots=` or `--boots rectangles.json`.
Terrain is limited to 0.012 mm above the body inside each rectangle, with a
smooth 0.3 mm transition outside it and an extra cell-width sampling margin.
The current archers deliberately use **no boot-clearance mask**, at the user's
request: the natural ground continues around and slightly up their boots,
without flattened depressions. Solo archers, all ten variants and the sergeant
reuse the gallery's unmasked soil surface; the archer strip uses
`aurelian.terrain-soil-natural-strip@2`. Their figure placements remain unchanged.
The visible archer soil uses feature scale 1.5 and relief amplitude 0.6 mm
(previously 1.0 and 0.25 mm). Solo archers and the soil gallery pin
`aurelian.terrain-soil-gallery@4`; these larger features make the ground readable
at miniature scale. Actual heights vary with the seeded field.
Regenerate
the surface with a new revision if the soles or their placement change.

All current layouts lift the complete figure once by 1 mm. Inherited model
sources subtract that same millimeter through `source.origin_mm`; overrides
retain their reviewed model coordinates. The migration baseline tests compare
every figure placement and part pin, including all ten archer variants and the
sergeant. Historical base definitions and saved review directories remain intact.

Review the named army layouts and **Bases - soil, sand, rocky, meadow and
magnets** at http://127.0.0.1:8765. The gallery orders surfaces left to right as
listed and places flipped solo and strip bodies below them to expose pockets.
Ctrl-hover identifies body and surface instances independently.

Verification uses `tests/test_terrain.py` for deterministic recipes, preserved
goldens, invalid configurations, cache identity, boot regions and migration
baselines. After composing the named reviews, run `tests/terrain_scene_probe.py`
with background Blender to check evaluated footprint bounds, recess rays,
terrain overlap, lowered boot regions and grounded, visible sole geometry.
`TERRAIN_PROOF_ROOT=out` enables the saved-provenance integration check. Browser
coverage is in `viewer/terrain.spec.js`; `tests/test_heightfield.py` verifies
the procedural grid contract and terrain-only compiler cache dependencies.
These checks remain visual geometry
checks and do not establish print readiness.
