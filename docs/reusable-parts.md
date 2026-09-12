# Reusable parts and visual assembly

Design the part first, then place it in models. The visual workflow does not
rebuild a regiment when one crest, helmet, torso, shield or weapon changes.

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

## Later publication or release

Keep working models visual-only until release work is requested. Release
preparation must materialize the selected modular composition, package its
dependencies, and perform the applicable export/print checks. The historical
`regiment build` commands still build their pinned whole-spearman recipes;
they do not automatically include newer modular part revisions. Do not use
those old recipes to release a subsequently changed modular model.
