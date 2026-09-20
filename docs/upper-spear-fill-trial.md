# Upper spear and helmet-side fill experiment

The user reported that separate, spaced prints and reducing nozzle temperature
from 220°C to 205°C improved the result. The remaining problem areas were the
upper spear and the gap above the rounded shoulder, between spear and helmet.
This experiment changes those areas; the accepted intact-spear target remains
unchanged. It does not depend on filament drying.

At the accepted 130% print scale:

- The upper shaft increases from 1.56 to 2.08 mm diameter, with a tapered
  transition above the hand. The lower shaft, spear axis and length are retained.
- The spearhead and collar widen to match the upper shaft. The terminal cap
  grows from 0.884 to 1.092 mm across before its existing profile flattening.
- Each of the five poses gets a new rounded fill rising from the shoulder/torso
  into the helmet-side gap and joining the spear. The fill is an elliptical
  primitive taper with a rounded cap, joined by ordered Exact CSG. Existing
  helmet, face, hand, sleeve and figure placements are retained.
- The existing glue-in footings are unchanged and fit both base variants.

The print trial contains five combined versions and one **pose 1, thicker spear
only** comparison. Compare that pair to assess the added fill at the same
temperature and shaft thickness. Compare the thick-only figure with the earlier
accepted print to assess the upper enlargement, allowing for any temperature
differences. The new geometry is a hypothesis to test, not a demonstrated fix
for blobbing or other extrusion errors.

Generate pinned definitions and assemblies with
`py -3.13 scripts/generate-upper-spear-trial.py`. Review the experiment under
**Trials & kits** in the local viewer. Source dimensions stay at recipe scale.
Files under `out/upper-spear-fill-20260919/` include the already-scaled STL files
and `upper-spear-filled-gap-205C.3mf`; do not scale them again.

The project uses PrusaSlicer 2.9.6, XL tool 2, 0.25 mm nozzle, PLA, 0.05 mm
layers, 205°C first and subsequent layers, supports off, and sequential printing
with 115 mm center spacing. It inherits the accepted project's remaining
settings and preserves the XL collision limits and installed presets.

These are **unchecked Blender Manifold union exports**, not digitally validated.
The five joins were reviewed from front, side, rear and overhead in the local
viewer. Evaluated Exact intersection checks found positive overlap from every
fill into the torso, head, helmet and spear. Pinned-definition, pose-preservation
and accepted-target regression checks pass.
The saved project is reopened and sliced without a separate configuration.
The new geometry still requires a physical print trial.
