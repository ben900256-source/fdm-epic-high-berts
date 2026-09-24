# Accepted infantry design across the army

The spearmen are now [locked with inclined spears](locked-spearmen.md). Their
latest accepted shapes and the final placement-only adjustment are pinned there.

The 2026-09-22 update applies the [accepted five-spearman design](wider-shield-trial.md)
to all **49 reusable figure recipes and 15 current layouts**: spear and short-sword
variants, forward spearmen, archers and elevated bows, swordmasters, command
figures and the Dragon Prince. The original five printed poses remain unchanged
in the historical wider-shield trial. The default composition now includes
the subsequent [fuller-head and facial-detail revision](bolder-faces.md).

Shared faces use the broader head with deeper eyes and mouth; infantry helmets
use the clearer opening. Command and cavalry helmet revisions enlarge the
opening while retaining their ornaments. Armoured infantry share the coarse
mail, broader torsos and chest plates. Archers keep their cloth tunics, broadened
15%; swordmasters and cavalry keep their own broader cuirasses.

New arm parts enlarge sleeves and hands while keeping grip landmarks and held
equipment fixed. Elbows move 0.30 mm outward in the local horizontal plane where
an elbow landmark exists. The existing aiming, drawing, sword, horn and hawk
poses remain. Nearby upright spears get fitted shoulder/helmet joins; distant
or lowered weapons do not receive a spanning fill.

Infantry shields use the wider shield and **raised flat seahorse revision 4**.
Shield yaw is limited to 20 degrees relative to the torso for this propagation;
this is an implementation choice for modest facing variation, not a new printing
gate. Cavalry retain their diamond shield and stronger scale/gem decoration.
Spears use the accepted uniform 1.4 mm source shaft and fuller faceted head.
The lance and standard pole receive uniform shafts and matching leaf decoration.

The default infantry, archer unit and center-standard unit use the matching
five-recess base spacing. Solo/gallery infantry bases use the matching glue-in
footing. Cavalry and forward-spear terrain extensions retain their own bases.
The workshop's separate compact-row exporter retains its historical strip and
magnet options; it resolves the updated figures. Those compact combinations need
their own fit review before printing.

## Sources and verification

- [Index](../specs/accepted-army-index.json): all current recipes, replacement map,
  98 new immutable parts, shield facing records, seed 1001 and export scale 1.3.
- [Frozen sources](../specs/accepted-army-sources.json): resolved recipes from
  `69eb30c`; regeneration cannot compound the changes through inheritance.
- `py -3.13 scripts/generate-accepted-army.py` regenerates pinned definitions,
  current assemblies, per-model compositions and golden hashes.
- Prior component revisions, trial definitions and saved reviews are retained.
- All 15 layouts passed saved-Blender provenance checks and viewer revision
  checks. Gallery review includes front and side views of all variant poses.
- Local equipment-contact probes found overlap for all 81 checked arm/equipment
  pairs, including both sword grips, bow grips, horns, hawk, shields and lance.
- The current recipe/golden/attachment-landmark tests and workshop tests passed
  (26 tests). This does not claim the full historical revision test suite was run.

Local review evidence is in `out/accepted-army-review-20260922/`. Only changed or
missing parts were compiled; existing cached geometry was reused. All new army
reviews are **visual-only**, with `VISUAL_PREVIEW` and empty `EVALUATED_EXPORT`.
No manufacturing union, slicing, independent repeat geometry build or new
physical trial was performed. Physical acceptance still applies only to the
original five-spearman print.
