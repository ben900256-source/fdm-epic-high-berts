# Locked spearmen and inclined spears

On 2026-09-23 the user accepted the latest five spearmen as the design baseline:
"they're good as is." The latest print made little noticeable difference, so
further face, helmet, crest, shield and body experiments stop here unless requested.

The accepted shape is saved in
[the printed five-pose snapshot](../specs/experiments/locked-spearmen-printed-row-20260923.json).
It includes the recessed head and restored nose, pointed helmet revision 5,
crest revision 7, raised fierce seahorse revision 6, wide shields and the uniform
shaft with decorative spearhead revision 3. Shield orientations, hands, bodies,
footings, terrain, source scale and shared base remain pinned.

The user's final change is that no spear should be perfectly vertical. The three
nearly upright poses were only 0.4, 1.4 and 1.8 degrees from vertical. They now
lean at least 6 degrees, with a sideways component visible from the front.
Each spear rotates about the point on its shaft nearest the grouped-finger
landmark. This preserves its seating in the existing hand. The two already
inclined poses remain at approximately 15.1 and 11.16 degrees.

The same placement rule applies to the reusable spearman variants and the
center-standard unit. Existing forward and more inclined poses remain unchanged.
It is implemented in `fdm_sculpt/components/leaning_spears.py` and applied by
`scripts/generate-accepted-army.py`. It reuses every immutable part cache;
no component geometry is regenerated. The standard pole is not a spear.

[The baseline record](../specs/spearmen-locked-baseline.json) pins the current
composition and separates the user's acceptance of the printed shape from the
new spear angles. The angle change is a visual iteration pending a physical
trial. No manufacturing validation or slicing is claimed for that change.

[Review the current spearmen](http://127.0.0.1:8765/?review=aurelian-spearmen-organic-faces).

Verification: 30 focused tests passed. All 41 current spear placements have at
least 6 degrees of lean; only 13 spear mounts changed across their repeated
recipes. Three saved/published layouts reused all cached parts and passed
provenance checks. Front, side and overhead viewer checks verified the loaded
mounts. All 40 local hand/shaft and shoulder/helmet-fill contacts overlap.
See the [visual verification record](evidence/locked-spearmen-visual-20260923.json).
