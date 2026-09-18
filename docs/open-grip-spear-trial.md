# Centered separate spears with deeper open grips

**Retired experiment.** The user accepted the physically printed
[130% intact-spear target](intact-spears-130-trial.md). This document and its pinned
definitions retain historical evidence; these grips are not the current target.

This is a **visual-only** fit prototype. Each spear axis now crosses the original
grouped-finger landmark. The current arm placements, shoulder and wrist seats,
spear directions, row stagger and 20 x 5 mm base remain pinned. The previously
reviewed fifth-arm shoulder rotation is retained; no new pose adjustment is added.

The current hand has a rounded palm, curled fingers with backing stock beneath
their relief, a thumb, and a palm heel attached at the original cuff.
Its front-facing open seat targets a
0.65 mm recess, 1.20 mm opening (0.10 mm clearance per side around the 1 mm shaft),
0.10 mm clearance behind the flat spear face, approximately 0.50 mm finger roots
and 0.75 mm palm backing. The spear rolls around its unchanged length axis to put
its flat face against the palm. It translates sideways into the seat and is glued;
there is no snap fit, closed socket or external adapter.

The shared `clearance_profile()` owns the shaft and wider spearhead envelopes for
the entire 15 mm approach from free space. Each neighboring part revision applies
local Exact differences only to geometry roles intersected by that envelope.
Pinned target source hashes reject stale clearance selections. These trial parts
are owned independently of the army recipes, and unchanged parts retain their
immutable caches. Earlier saved reviews and part revisions are preserved.

The separate spears remain 13.6 mm long, 1.0 mm wide and 0.8 mm high in printing
orientation, with rounded upper profiles and flat undersides. The five-spear sprue
still uses only butt gates. The row retains its front-to-back stagger: figure 1
moves back 0.25 mm, figure 2 forward 0.40 mm and figure 5 forward 0.45 mm.
Deleted thick-shaft and large-socket trials stay deleted.

Use **Trials & kits** in the local viewer:

- `open-grip-spear-assembled-trial`: seated full spears.
- `open-grip-spear-row-trial`: empty grips and clearance cuts.
- `full-rounded-spear-kit-trial`: unchanged butt-only sprue.

Definition tests cover source landmarks, unchanged poses, shaft-axis centering,
shared clearance, revision hashes and resolver checks. The saved-scene probe
`tests/open_grip_scene_probe.py` measures the evaluated hand surfaces, checks the
continuous insertion envelope against every figure, and checks contacts between
surviving mesh shells without fusing the strip. Atelier separately reopens each
saved scene to verify component and operation provenance. These checks do not
replace manufacturing gates, slicing or physical fit trials.

```powershell
py -3.13 scripts/generate-open-grip-spears.py
py -3.13 -m pytest tests/test_open_grip_spears.py -q
py -3.13 -m fdm_sculpt.atelier compose specs/experiments/open-grip-spear-assembled-trial.json --seed 1001 --output <fresh-directory>
```

## Original centered review results

The first centered trial pinned grip revisions `@5` (pose 2 used `@7`) and neighboring clearance revisions
`@1`, with `row-04-skirt-trial@2` removing one detached cut-off mail tip.
Saved rows are `out/centered-grips-20260917/assembled-v7` and `empty-v7`.
The assembled scene's `grip-fit-probe.json` records the evaluated checks. It also rejects palm geometry outside its primitive envelope and neighboring difference results outside their source bounds:

| Measurement | All five grips |
| --- | --- |
| Axis distance from original finger center | Less than 0.001 mm |
| Recess depth | 0.650 mm |
| Opening width | 1.200 mm |
| Clearance per side / behind flat | 0.100 mm / 0.100 mm |
| Palm backing | 0.750 mm |
| Finger roots | Approximately 0.527 mm |

All five palms are single connected pieces attached to their preserved sleeves.
Every figure remains connected, and the full approach envelopes have no
intersections with figure geometry, neighboring figures or neighboring spears.
The one isolated cut chip was removed using a local Exact box difference;
no mesh elements were hand-edited. The palm crosses the seat cutter before the difference to avoid coincident faces. Pose 2 cuts the individual closed hand primitives before joining them; its earlier compound cut produced an Exact Boolean artifact that was caught in visual review. These are visual fit and contact checks only.

Eight focused grip/hand tests and both cache-integrity tests pass. The broader
parts suite has two existing failures expecting older left-arm references in the
unchanged main army assembly (`test_inward_nose_and_shield_hand_revisions` and
`test_arms_reach_shield_backs`). They are unrelated to these trial definitions.

The viewer's figure-isolation condition now produces a Boolean for ordinary
figures, so hidden neighbors are actually excluded by Three.js. Close grip
inspection uses hidden shields and camera clipping to expose the seat beneath
the spearhead; full-row views retain all equipment.

Both final saved-scene provenance checks pass. The assembled and empty compositions compiled zero parts, reusing 80 and 79 cached parts respectively. The browser verified the published revisions and captured all 30 close front, side and overhead views in `out/centered-grips-20260917/viewer-check.json`; the two contact sheets and full-row views are saved beside it.

## Tapered undersides

Grip revisions `@9` (poses 2 and 4 use `@10`) add backing stock beneath the
curled finger relief. Four local Exact plane cuts taper
the underside toward the existing cuff at 45 degrees in the upright printing
orientation. The planes follow world vertical, including the leaning fourth
pose. Hand placements, spear axes, shared insertion channels, neighboring part
revisions and the separate spear kit are unchanged.

The full 0.65 mm recess is retained at the upper gripping wall, sampled 0.45 mm
above the original finger-center landmark. Lower fingers deliberately tuck back
toward the wrist; they no longer retain the full recess depth. The fit probe
records that sample position explicitly and still checks the 1.20 mm opening,
0.10 mm clearance, 0.75 mm backing, wall roots, attachment and full insertion
path. Later experiments with larger continuous walls and engraved grooves were
discarded: they made the hand blocky without improving the sliced results.

The current saved visual scenes are `out/tapered-grips-20260917/assembled-v11`
and `empty-v11`. Both preserve empty `EVALUATED_EXPORT` collections. They reuse
the unchanged component caches. The saved provenance checks use the same
checks with each immutable definition digest memoized, avoiding repeated
hashing of large terrain and mail definitions.

The companion `prusa-v11` directory contains an unchecked Blender Manifold
export and a two-object PrusaSlicer **2.9.6** project. The targeted comparison
slices the earlier and tapered rows with the same tool-2 profile and applies the
existing deposited-toolpath criteria in each grip neighborhood. This diagnostic
does not replace full manufacturing validation or physical fit testing.

Final evaluated fit and attachment checks pass for all five hands, including
the unchanged insertion paths. Both saved-scene provenance checks pass. The
20 focused unit tests pass; the existing whole-proof integration test is
skipped because no manufacturing build was requested. The viewer review covers
all five hands empty and assembled from front, side and overhead.

With identical 2.9.6 slicing settings, unsupported toolpath length flagged in
the five grip neighborhoods falls from **16.659 mm to 7.593 mm** (about 54%).
Flagged runs fall from 29 to 20. The sampled neighborhoods also include adjacent
figure geometry, so these totals are not exclusive measurements of the hands.
Small support flags remain: this revision is an improved visual/fit prototype,
**not a support-free or digitally validated print**.
