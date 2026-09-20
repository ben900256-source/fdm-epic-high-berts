# Broader infantry and more readable detail

The user reported that the printed figures reproduce the intended design well,
but faces, chainmail and insignia lack definition. Spear handling is now a lower
priority. This separate visual study starts from the filled-gap upper-spear
trial and retains its equipment, helmet outline, footings and figure height.

- Torso and breastplate widen 15%. The upper mail skirt broadens while its
  lower backing, hem transition and foot positions stay fixed.
- Eye recess height increases from 0.26 to 0.39 mm at print scale. The mouth
  cutter height increases from 0.169 to 0.312 mm. The long nose projects further
  and the chin is fuller. These are primitive dimensions, not measured sliced
  openings; the helmet is unchanged.
- Seven rows of sixteen larger mail links replace thirteen rows of thirty.
  Each link is nominally 0.845 mm wide and 0.91 mm high at print scale, with
  a recessed eye and solid backing. The fewer, larger links are intended to
  remain recognizable after printing.
- Seahorse relief depth grows 45% about its embedded back plane; strokes widen
  18%. The corresponding underside ramps grow with the relief.
- Upper bodies and their attached equipment turn by -16, +14, 0, -12 and +18
  degrees around the vertical axis. Head counter-turns reach 18 degrees, and
  shield arms turn up to 12 degrees around their shoulder roots. Helmet-to-spear
  fills are refitted for each pose. Feet stay planted. The center figure provides a
  comparison with unchanged pose so the proportion/detail change is clear.

Generate definitions with `py -3.13 scripts/generate-readable-infantry.py`.
All ten new component IDs pin revision 1. Existing definitions and accepted
print targets are preserved. The gallery and direct comparison are under
`specs/experiments/readable-infantry-*-trial.json`; source scale remains 1x.
The existing 1.3 export enlargement must be applied exactly once for printing.

These are **visual-only** reviews. Fewer links and larger features are design
hypotheses; sliced detail and another physical trial must establish improvement.
Wider bodies and changed equipment positions also need renewed assembled-row
clearance checks before using the existing shared bases. Footing dimensions
are unchanged, but that alone does not establish complete figure/base fit.

Local review: `out/readable-infantry-20260919/`. Isolated head, mail and insignia
reviews and both assembled scenes pass saved-Blender provenance checks. The
gallery and comparison revisions were verified in the Three.js viewer, with
front, side, rear, overhead and detail views captured. Golden/resolver checks,
fixed-foot and vertical-placement checks, relative hand/equipment transforms,
and the accepted print-target regression pass. No manufacturing union, slicing
or new physical-print validation was performed for this visual study.

## Overhang recheck — 2026-09-19

The user's requested overhang recheck found **increased geometric risk in the
new face, mail and insignia** on all five poses. Earlier passing checks covered
definitions, assembly and grip alignment, not unsupported extrusion.

The read-only screen used cached evaluated meshes at the 1.3 print scale,
sampled triangle centers on downward surfaces steeper than 45 degrees from
vertical, masked surfaces inside overlapping parts, and ray-tested clearance
below each remaining sample. The table totals sampled surface area with more
than 0.25 mm vertical clearance below, across all five figures. It is a
comparative geometry indicator, **not unsupported toolpath length, bridge span,
required support area, or a prediction of print failure**.

| Region | Previous trial, mm² | New detail trial, mm² |
| --- | ---: | ---: |
| Face | 0.091 | 1.027 |
| Mail skirt | 6.042 | 10.551 |
| Seahorse insignia | 4.119 | 7.546 |
| Shoulder/helmet fill | 0.000 | 0.000 |
| Right arm | 3.783 | 2.712 |
| Left arm | 0.771 | 0.208 |

Underside views in the local viewer confirmed the new nose's projecting lower
tip, the roofs of the larger eye/mouth recesses and mail-link eyes, and the
seahorse's snout, belly and tail undersides as the principal detail hotspots.
Widening the emblem's depth without lengthening its ramps makes those ramps
steeper. The refitted shoulder/helmet joins produced no flagged area under
this screen; that is not a support-free certification. Existing sleeve/hand
undersides still have flags, although their aggregate exposed area decreased.

Before the next print, revise the nose underside into a face-backed taper,
lengthen the emblem's lower ramps, and consider pointed/teardrop roofs for the
mail and facial recesses while retaining their readable openings. Actual
sliced bead support is still required to judge the short anchored spans.
No model geometry was changed during this recheck.

Evidence: `out/readable-overhang-check-20260919/surface-screen.json`,
`viewer-check.json`, and marked underside images. The viewer revision was
verified; twenty close views were captured. Triangle-centroid sampling and
normal-based overlap masking are approximate. No fusion, slicing or physical
trial was performed.
