# Separate figures with glue-in bases

This variant keeps the accepted intact-spear figure geometry and 130% print scale.
Each figure gets a flat 5.2 × 6.5 × 1.3 mm footing with its original terrain
cropped to that footprint. The figures can be spaced apart on the printer and
glued into either of two shared bases:

| Option | Printed outside dimensions | Seating |
| --- | --- | --- |
| Compact tray | 28.7 × 8.4 × 2.0 mm | One shared recess; leave 0.2 mm between footings |
| Individual recesses | 32.3 × 8.4 × 2.0 mm | Five pockets at 6.3 mm center spacing |

Both have 0.8 mm floors and outer walls, 1.2 mm recess depth, and 0.15 mm
clearance per side. The wider version also has 0.8 mm dividers. Footings finish
0.1 mm above the rim. The compact tray's 0.15 mm end clearance is for the whole
row; the individual-pocket version gives each footing that allowance.
These are glue fits, not snap fits. Dry-fit before applying glue, and remove
any brim or first-layer flare from the footings. Position figures 1–5 left to
right as in the assembled review; the compact tray does not key their order.

`scripts/generate-glue-base.py` publishes immutable base and terrain parts,
individual figure assemblies and both assembled reviews. The accepted
`specs/elf-print-target.json` remains the reference; this is a separate trial.
Source assemblies stay at recipe scale. Exported STL and Prusa projects already
include 130%; do not enlarge them again.

Local output: `out/glue-base-20260918-v2/`. It contains five individual figure STLs,
both base STLs, a spaced project and a sequential project. The projects use
tool 2, the saved XL nozzle array, 0.25 mm nozzle, PLA and 0.05 mm layers, with
supports off. Figure centers are 115 mm apart on the print bed. Settings are
copied from the saved accepted print project; installed presets are unchanged.

Sequential printing finishes one object before starting the next, reducing
travel between figures. Prusa describes it as a way to reduce stringing and
requires suitable extruder clearance; the project retains the saved XL's
67 mm radius and 21 mm height limits. See
[Prusa's sequential-printing guidance](https://help.prusa3d.com/article/sequential-printing_124589).
The regular spaced project retains layer-by-layer printing as an alternative.

The exported figures were checked seated in both bases using evaluated Exact
intersections. The final 5.4 mm compact spacing and 6.3 mm pocket spacing showed
no positive-volume overlaps between figures or with the base. This is an
assembly interference check, not a manufacturing mesh certification. The saved
sequential project was reopened and sliced without a separate configuration.

Review the assembled options and separated pieces in the local viewer's
**Trials & kits** tab. These reviews display source dimensions. The outputs
are **unchecked Blender Manifold union exports**, not digitally validated.
The new footing/base fit and sequential print quality still require a physical
trial; acceptance of the earlier fused row does not establish those results.
