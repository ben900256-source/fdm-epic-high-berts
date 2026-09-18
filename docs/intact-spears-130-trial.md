# Accepted intact spear print target

The user reported that this version printed better and was good enough, and
selected it as the new target. This is user-reported physical print acceptance,
not a claim that the full digital validation gates passed. The separate-spear
and open-grip experiment is retired; its saved source history remains available.
The machine-readable default is [`specs/elf-print-target.json`](../specs/elf-print-target.json).

User-requested physical trial: take the intact 1.2 mm shaft design and enlarge
the complete row uniformly by 30%. The source uses the original closed hands
and full spears, without separate-spear grip openings or clearance channels.

- Source: `specs/experiments/intact-spears-130-print-trial-source.json`, seed 1001.
- Spear: historical `aurelian.spear-shaft-trial-120@1`, restored unchanged.
- Export scale: 1.3 on the complete fused row, including terrain and base.
- Nominal sole-to-eye height: 10.4 mm; shaft diameter: 1.56 mm.
- Base: 26 × 6.5 × 1.3 mm, excluding terrain relief.
- Output: `out/intact-spears-130-20260917/`.
- Project: `intact-spears-130-unchecked.3mf`.
- STL: `intact-spears-130-unchecked.stl`.
- PrusaSlicer 2.9.6, XL tool 2, 0.25 mm nozzle, PLA, 0.05 mm layers,
  supports disabled. Installed presets are unchanged.

The local viewer review is explicitly the unscaled cached source. The enlarged
STL and slicer project are the physical trial artifacts. Saved-source provenance
and front, side and overhead viewer checks accompany the output. The saved
project is reopened and sliced without a separate configuration.

Unchecked Blender Manifold union output, not digitally validated. The accepted
result is specific to this row and print setup. Other retired spear experiments
remain retired. Source recipes and the general row builder still use the original
dimensions; apply 130% once when reproducing this target, never again to the
already enlarged STL or project.

The public [print record](evidence/intact-spears-130-accepted.json) records the
source and artifact hashes, dimensions, slicer settings and user-reported result.
Generated meshes, local profile snapshots and scratch files stay out of Git.
