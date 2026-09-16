# Taller sergeant plumes and readable sword hilts

The later [additive fist revision](forward-spearmen-and-additive-fists.md)
replaces the clipped hands used for the hilt diagnostic measurements below.
Those measurements have not been repeated with the newly restored fists.

The current visual review uses `aurelian.sergeant-helmet@6` and
`aurelian.shortblade@7`. Generate their pinned definitions with
`py -3.13 scripts/generate-crown-and-hilt.py --seed 1001`.
The source manifest and golden hashes preserve the intermediate revisions.

The six feather bodies are 35% longer about their existing roots. Width,
depth, sweep and broad Exact tip cutoffs are preserved. The ordinary helmet
peak, face opening and nape remain unchanged. On the hawk sergeant, the
two plume tops rise from Z 10.831/10.795 to 11.529/11.486 mm.

The short sword exposes a cylindrical handle above the fist. Its guard is
1.5 mm wide, reduced from 1.85 mm, and the blade and guard sit 0.55 mm higher
on the handle. An elliptical collar grows only beneath the upper guard;
the full-height triangular grip web is removed. The shortened lower hilt
seats its pommel against the hand. Grip mount and hand placements are fixed.

## Visual review and focused diagnostics

`out/taller-plumes-readable-hilt-v7-gallery` is the assembled visual review,
with viewer revision
`f68b044848e5e3fb7ed0cf7e2660a08ba958a6d4af99e744a81edc76371b3f13`.
The live Three.js viewer loaded this revision without errors. Its saved
Blender provenance passed, and all 20 hands contact sleeves and held items.
Only changed parts were compiled; the gallery reused 64 cached parts.

The plume diagnostic in `out/plumes-hilt-after-v5` uses the same helmet
revision 6. With PrusaSlicer 2.9.5, tool 2, a 0.25 mm nozzle and 0.05 mm
layers, its last deposited layers are Z 11.54 and 11.49 mm. Both plume
wings have material on every layer in the final 0.4 mm. Mesh tops are
within one layer of the deposited tops. The first layer is 0.14 mm.

The final hilt diagnostics are `out/readable-hilt-low-guard-v7` and
`out/readable-hilt-sergeants-v7`. Blue overhang extrusion-path lengths in
component-local regions are:

| Pose | Pommel | Grip | Crossguard |
| --- | ---: | ---: | ---: |
| Sword low | 0.1609 mm | 0 mm | 0.0294 mm |
| Sword guard | 0.2907 mm | 0 mm | 0 mm |
| Sword raised / sword sergeant pose | 0 mm | 0 mm | 0 mm |
| Hawk sergeant | 0 mm | 0 mm | 0 mm |

The remaining low/guard-pose segments are on the lower pommel at Z 5.19
and 5.94 mm in these diagnostics, plus a tiny low-pose crossguard corner.
These lengths describe blue toolpaths, not unsupported cantilever distances.
For comparison, the original low-pose guard had 0.083 mm, the guard-pose
crossguard 0.5267 mm, and the hawk-sergeant pommel 0.6819 mm of blue paths.
The remaining pommel areas still need design attention before claiming
support-free printing; the grip's visible outline is preserved in this review.

An earlier two-sergeant diagnostic exposed a separate omission near the
unchanged narrow sword terminal: it skipped Z 11.59-11.84 before a small
path at Z 11.89. The strict layer parser rejected that diagnostic. No gate
was changed. Adding the tall standing spearman keeps the later diagnostic's
overall layer sequence populated; it does not establish sword-tip deposition.
The plume-specific checks above are independent of that sword terminal issue.

These diagnostics use unchecked Blender Manifold output. Saved Prusa
projects were reopened and sliced without a separate configuration;
installed presets were unchanged. They are local design checks, not full
manufacturing validation or a physical print trial.
