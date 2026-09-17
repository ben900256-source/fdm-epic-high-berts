# Flat spear and detachable upper-section trial

The current trial is `specs/experiments/flat-spear-kit-v2.json`, seed 1001.
It is a separate experiment; army figure recipes have not been changed.

The kit contains four flat-backed spears and nine upright blind sockets.
With the socket block above the sprue and its raised tick marks on the left,
the spear columns run left to right:

| Column | Piece | Shaft section |
| --- | --- | --- |
| 1 | Full-length separate spear | 1.0 mm wide × 0.8 mm thick |
| 2 | Full-length separate spear | 1.2 mm wide × 0.8 mm thick |
| 3 | Detachable upper section | 1.0 mm wide × 0.8 mm thick |
| 4 | Detachable upper section | 1.2 mm wide × 0.8 mm thick |

The upper sections have a common 0.8 × 0.8 mm keyed pin, approximately
2 mm insertion length, and a 1.6 mm wide stop collar. Their eventual joint
would sit just above the figure's fist, retaining the integral hand and lower
shaft. This kit tests the interface before making that figure revision.
The cross-sections are chamfered rectangles, not round rods.

The two full-length shaft bodies retain 13.35 mm length; their flat diamond
heads are newly designed for this orientation. All four pieces have a flat
back on the bed. Each attaches to the frame with two 0.45 mm wide,
0.4 mm tall gates. Clip the gates at the shaft with flush cutters; avoid
twisting the long piece against the frame. No tabs touch the insertion pins.

## Fit tests

Rows are identified by one, two or three raised ticks. The one-tick row is
closest to the spears. Within every row, clearance increases left to right.

| Socket row | Intended piece | Left opening | Middle opening | Right opening |
| --- | --- | --- | --- | --- |
| 1 tick | Full 1.0 mm spear | 1.15 × 0.95 mm | 1.25 × 1.05 mm | 1.35 × 1.15 mm |
| 2 ticks | Full 1.2 mm spear | 1.35 × 0.95 mm | 1.45 × 1.05 mm | 1.55 × 1.15 mm |
| 3 ticks | Either upper-section pin | 0.95 × 0.95 mm | 1.05 × 1.05 mm | 1.15 × 1.15 mm |

These are total clearances of 0.15, 0.25 and 0.35 mm across each dimension,
equivalent to 0.075, 0.125 and 0.175 mm per side. They are experimental
targets, not measured printed fits. Socket depth is 2.4 mm. Test the loose
right-hand hole first and move left; do not force a tight joint. The upper
sections should stop at their collar. The full-length spears bottom in the
coupon holes; this is a fit gauge, not the final through-hand design.

Record which holes fit without force, rotational play, whether clipping
damages the shafts, and whether the flat spears still peel or bend too easily.
Compare the two widths using the same material condition and settings.

## Digital experiment results

Artifacts are in `out/flat-spear-kit-v2-20260917/`:

- `flat-spear-kit-v2.stl`: unchanged native Blender Manifold export.
- `flat-spear-kit-v2.3mf`: PrusaSlicer 2.9.5 project with embedded settings.
- `flat-spear-kit-v2.gcode`: diagnostic slice of the saved project.
- `prototype-checks.json`, `slicer-evidence.json` and `layer-review/`: evidence.
- `kit-view.png` and `viewer-check.json`: local viewer review.

The project uses tool 2, nozzle array `0.4,0.25,0.4,0.4,0.4`, 0.05 mm layers
after a 0.14 mm first layer, and zero generated supports. It uses the existing
proof PLA preset (215°C first layer, 210°C afterward), not confirmed settings
from the user's earlier failed print. A build-local first-layer extrusion width
of 0.25 mm replaces 0.32 mm. Installed presets were not changed. An exterior
6 mm brim is retained. The saved project was reopened and sliced without a
separate settings file; all recorded extrusion uses T1 (tool 2).

The CLI estimate is 55m 46s and 1.12 g PLA. The conservative deposited-path
screen has zero rejected unsupported runs. The initial 0.32 mm first-layer
width produced a 0.453 mm flagged run at the first full spear's butt on layer
Z 0.19 mm; using 0.25 mm cleared this without changing the screen's criteria.

All shaft/pin, clip-tab and socket witnesses pass. Five of 115 material/void
witnesses remain unfilled pixels inside spearheads on sampled layers; the
heads themselves retain deposited contours. These gaps still need physical
inspection. The strict mesh check also does **not** pass: analysis-only exact
coordinate welding and removal of 30 zero-area/collapsed triangles leaves 58
boundary edges. The exported STL was not repaired or rewritten. It is one
connected positive-volume component in that analysis, but is not certified
watertight. The slicer's ability to produce paths does not override this finding.

This is an **experimental fit/handling coupon, not a digitally validated or
physically tested print**. No independent-repeat manufacturing gate or full
self-intersection validation was performed. Two resolver/hash/interface tests
pass, and saved Blender provenance and the loaded viewer revision were checked.

## Reproduction

```powershell
py -3.13 scripts/generate-flat-spear-kit.py --revision 2
py -3.13 -m pytest tests/test_flat_spear_kit.py -q
py -3.13 -m fdm_sculpt.atelier compose specs/experiments/flat-spear-kit-v2.json --seed 1001 --output <fresh-review-directory>
```

Revision 1 remains pinned for comparison. Revision 2 adds only the insertion
stops to the two upper-section parts, reusing the other four component caches.
