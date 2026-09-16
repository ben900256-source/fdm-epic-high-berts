# Forward spearmen and uncut fists

Ten new spearmen hold the existing long spear at 0, 5, 10, 15, 20, 25,
30, 35, 40 and 45 degrees above horizontal. They appear under Spearmen in
the individual model dropdown and row builder. The saved gallery is
**Forward spear variants (10)**, from `specs/elf-forward-spearmen.json`.

The grip is moved toward the shaft's rear so most of its length points
forward. Hands rotate with the shaft while their robe sleeves and shoulders
retain the reviewed pose. Each figure has a 4 by 18 mm base footprint: a
forward extension overlaps the ordinary 4 by 5 mm base. The default body
is 1 mm thick with 0.5 mm terrain relief. Rows with magnet pockets use a
2 mm extension grounded at Z zero, without filling the strip's pockets.

Four permanent rests per spear use narrow forked deadwood stems and root
stones. Three stand ahead of the hand; one supports the short rear section.
The load-bearing ends are at least 0.75 mm across. Small decorative twig
ends narrow further. These are permanent terrain, as requested, and have
no breakaway necks or removable support designation. The higher-angle poses
need taller stems; their strength and the spans between rests need print
trials before any print-readiness claim.

## Fist treatment

All 25 arm definitions affected by the earlier fist cutoffs now use new
revisions. The `fist_rising_envelope` operand and its intersections are
removed. Every original palm, finger, thumb and glove primitive, including
its frame and grip landmarks, is preserved. Beveled conical additions rise
from the sleeve beneath these shapes using ordered Exact unions. The
regular infantry and all ten forward poses receive this additive treatment.

`specs/additive-fists-sources.json` and its golden fixture pin the previous
arms. `scripts/generate-additive-fists.py --seed 1001` regenerates the new
definitions and updates their live references. The forward recipes use
`specs/forward-spearmen-sources.json`, with pinned hand, spear, body and
review replacements; `scripts/generate-forward-spearmen.py --seed 1001`
regenerates them. Previous terrain-rest revision 1 and its source manifest
remain available.

## Review evidence

- `out/additive-fists-v1-gallery`: regular infantry with uncut hands.
- `out/forward-spearmen-deadwood-v2-gallery`: all ten low-spear poses with
  the additive fists and forked terrain rests.
- Golden hashes, resolver checks, angle/base coverage and both row-base
  thickness choices pass the focused Python tests.
- Background Blender contact probes check 40 hand-to-sleeve and
  hand-to-equipment relationships across the two galleries, plus all 40
  spear-rest and root-to-base contacts.
- The live Three.js viewer exposes all ten variants, including a complete
  underfoot base in the individual preview. Cached geometry is reused;
  only changed parts are compiled.

These are visual-only reviews with saved provenance and empty
`EVALUATED_EXPORT`. No manufacturing fusion, mesh printability audit or
slicing was performed for this revision. Earlier sliced results for the
clipped hands do not apply to the new additive fist geometry.
