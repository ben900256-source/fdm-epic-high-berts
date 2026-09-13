# Printability criteria for the elf proof

The target is an upright single-piece strip on the five-tool Prusa XL, using
tool 2's 0.25 mm nozzle, PLA, 0.05 mm layers and the preserved 0.14 mm first layer.
The design target is **zero removable supports**. The 6 mm adhesion brim is
separate from support material. Digital checks identify candidates for a trial;
they cannot predict cooling, adhesion, surface finish or handling strength.

After generating and slicing a fresh build, run:

```powershell
py -m fdm_sculpt.regiment assess out/elf-v10-trial --support-audit
```

This writes `printability-review.json` and the evidence below. A failed screen
returns a nonzero exit code and retains its diagnostic artifacts for inspection.
Full `validate --compare` remains necessary before digital validation.

## Geometry and fine detail

- One connected, watertight, outward-facing, positive-volume manifold solid;
  no self-intersections or export face removal.
- At least 0.75 mm structural stock, 1.0 mm shafts, 0.25 mm attached relief and
  0.5 mm intentional clearances. Tapered tips and decorative recess edges are
  separately inspected at their actual sliced size.
- Named evaluated-mesh probes verify head/helmet fill and eye recesses, grips,
  forearm joins, shoulder cloth, shields, shafts and inter-figure spacing.
- Preserve the printer's nozzle array; validate index 1 and `T1` model extrusion.
  A nonempty STL or a successful slicer exit is insufficient.
- Every intended solid contour must retain deposited paths. Inspect nose, eyes,
  mouth, insignia and terminal spear/helmet layers at enlarged scale.

For the fitted-head revision, five sampled pixels at each named eye, mouth,
nose and brow landmark check whether the actual deposited layer contains the
expected recess or solid material. This creates 25 feature checks for the strip
in `previews/face-layer-evidence.json`, supplementing whole-contour survival.

## Terminal tips

For future spear and banner-pole finial revisions, use an upward-narrowing
taper ending in a small flat or rounded cap. A taper that stays over the
material below it does not introduce an outward overhang; a sideways-pointing
tip must be assessed in its actual printing orientation.

Start around **0.3-0.4 mm across the narrowest dimension of the terminal cap**.
This is a provisional design recommendation, not a validated minimum or a
replacement for the release gates. Measure the resulting geometry after
scaling and bevels, rather than using the primitive radius alone. Keep the
supporting shaft at least 1.0 mm thick; the thinner region is a short terminal
taper, not an extended thin stem.

The intended next adjustment is moderately sharper ordinary spear tips and
a slightly blunter banner finial. This recommendation has not yet changed
`aurelian.spear@3` or `aurelian.standard-pole@4`.

Inspect the last deposited layers for omitted detail and cooling artifacts,
then check handling strength in a physical trial. A 0.05 mm layer height is
vertical resolution, not a 0.05 mm printable width. Arachne may widen small
features or omit features below its configured minimum; a sharp viewer
silhouette alone is insufficient evidence.
[Prusa Arachne documentation](https://help.prusa3d.com/article/arachne-perimeter-generator_352769)

## Support screen

Prefer surfaces that grow no more than one layer height sideways per layer
(45 degrees from vertical). This is a conservative design aim, not a guarantee:
Prusa specifically notes that small 0.25 mm nozzles can require more conservative
overhangs. Use ramps, tapered undersides and solid joins beneath details.
[Prusa modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

`fdm_sculpt.printability` samples G-code centerlines every 0.025 mm against the
previous layer's deposited bead footprints. This is stronger evidence than
testing support against the intended mesh, which may contain unfilled space.
One 0.025 mm cell is allowed for raster uncertainty. Centerline support roughly
corresponds to half the new bead resting on existing plastic.

Uncovered runs require either a short local ledge (at most 0.25 mm with an
anchor) or a nearly straight bridge anchored at both ends. External bridges
are limited to 1.0 mm; internal infill bridges to 5.0 mm. An unsupported closed
loop may not be hidden by splitting it at the G-code seam. These are provisional
engineering screens to calibrate with physical trials, not printer specifications.

The existing mesh-layer screen also rejects floating contours, missing paths
and local lateral growth beyond 0.25 mm. These complementary checks produce
`previews/printability.json`, `previews/support-hotspots.png` when risks exist,
`previews/layer-evidence.json` and the sliced-layer proof sheet. Support hotspot
images show the worst flagged layers in red, with coordinates in the report.

Actual extrusion width matters: Arachne can widen thin features and omit ones
below its configured minimum. Keep the installed settings snapshot and inspect
the generated paths instead of equating nominal nozzle size with printable
detail. [Prusa Arachne documentation](https://help.prusa3d.com/article/arachne-perimeter-generator_352769)

PrusaSlicer's automatic support analysis is useful as another review: it checks
extrusions and factors such as bridging, adhesion and stability. It does not
replace the checks above or a trial print.
[Prusa support analysis](https://help.prusa3d.com/article/paint-on-supports_168584)

`fdm_sculpt.prusa.support_audit(build)` also produces a separate diagnostic slice
with automatic organic supports at 45 degrees from the bed. Its report counts
support filament relative to model filament, separating the adhesion brim.
This provides a reproducible support-cost comparison between geometry revisions.
The diagnostic G-code is not an approved print file and never replaces the trial
project. Automatic supports may be unnecessarily conservative around tiny
details; review their contact locations and removal access.

## Trial and reuse

Review the complete strip, head detail and layer evidence before printing.
Record the first trial's nozzle, material, temperatures, cooling and speeds.
Inspect the brow/nose undersides, eyes and mouth, seahorse curls, cape hems and
spear tips for droop, lost detail or breakage; handle the strip as a game piece.
Adjust recipes or the build-local print settings, repeat the same seed and
compare hashes. Only promote the design grammar into other units after visual
and trial-print acceptance.

A passing manifest is labeled **digitally validated**. Unresolved support
flags keep the candidate in review even when the geometry passes its checks.

## Revision 10 findings — seed 1001

The fitted-head strip passes topology, self-intersection, structural and
head-fill probes. Its production profile slices successfully into 258 layers
on tool 2, with a 43 minute 55 second time estimate. These successes do not
override the failed printability screen.

| Measured diagnostic | Previous revision 9 | Fitted-head revision 10 |
| --- | ---: | ---: |
| Automatic support/model filament, excluding brim | 36.2% | 31.3% |
| Unaccepted runs in the conservative support screen | 204 | 163 |
| Uncovered toolpath centerline | 234.477 mm | 199.676 mm |

The automatic-support comparison uses identical 45-degree organic-support
settings. Its ratio is an estimate of support quantity, not a probability of
print success or proof that every flagged area needs support.

Of the 25 facial witnesses, 21 pass. Both eye recesses, the mouth recess and
the filled brow survive on all five figures. Four nose witnesses fail: a
mesh/toolpath overlay confirms that the slice rounds away much of the narrow
nose projection. Explicit 0.2125 mm minimum bead and 0.0625 mm minimum feature
settings, shorter Arachne transitions, and Classic with thin-wall detection
were separately tested; none preserved all five nose witnesses. The production
profile remains unchanged by these diagnostic experiments.

The mesh-layer screen flags 14 layers, including disappearing small contours,
one floating contour and excess local growth near Z 7.9–8.0 mm. Terminal helmet
detail is also lost on several layers. Spear paths survive the checked upper
layers. Support-screen red paths are concentrated at several low/body layers
and around the neck/head transition; some internal paths may receive useful
same-layer support that this conservative screen does not model.

The next geometry priorities are a wider printable cross-section for the shared
long nose, supported transitions beneath projecting details, and investigation
of the disappearing contours. Preserve the approved helmet outline and overall
poses while revising their local construction. This is a **visual proof with
failed printability gates**, not a support-free or digitally validated print.
