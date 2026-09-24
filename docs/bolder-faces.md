# Fuller heads and stronger facial detail

The 2026-09-23 visual revision enlarges heads across the 49 current figure
recipes and 15 army layouts. Head width increases 8%, depth 5%, and height
stays unchanged. Eye height, all assembly mounts, equipment and poses are
preserved. The matching helmet bodies broaden slightly, retaining crown
height, the pointed outline and existing officer/cavalry ornaments.

- Shared head: `aurelian.readable-head-trial@4`.
- Infantry helmet: `aurelian.readable-helmet-trial@2`.
- Three decorated helmet families advance from accepted revision 1 to 2.
- Face-opening cutters grow from 1.20 x 2.30 x 1.86 to 1.34 x 2.50 x 1.98 mm
  in source coordinates, with a smaller 0.06 mm corner bevel.
- Eye cutters grow to 0.70 x 1.06 x 0.42 mm. The long nose becomes wider and
  projects further, retaining its existing tapered underside envelope.

Evaluated head geometry at the existing 1.3 print scale measures 2.224 mm
wide (previously 2.057 mm). At the eye-center ray, the eye floor sits 0.495 mm
behind the sampled brow surface (previously 0.387 mm). Nose projection from
that brow reference is 0.888 mm (previously 0.665 mm). These are local surface
probes, not claims about deposited detail or slicer resolution.

The generator `scripts/generate-accepted-army.py` applies the new face recipes
as a final step to its frozen sources, so repeated generation cannot compound
the enlargement. Old component definitions, golden hashes and historical
physical-test recipes remain available. Only five new parts were compiled;
unchanged cached parts were reused across every layout.

Verification: 29 focused tests passed; all 15 saved army scenes and the
before/after comparison passed provenance and viewer revision checks. Local
Exact contact probes found overlap in all 132 checked head/torso,
head/helmet, crest, plume and helmet-fill pairs. Front and side close-ups
cover the infantry, both officer helmet styles, elevated archer and cavalry.

Review the comparison at
[the local viewer](http://127.0.0.1:8765/?review=bolder-face-comparison-trial).
Saved local reviews are in `out/bolder-faces-review-20260923/`; portable evidence
is in [the verification record](evidence/bolder-faces-visual-20260923.json).

This is **visual-only**: `VISUAL_PREVIEW`, empty `EVALUATED_EXPORT`, no new
slicing or physical trial. The previously accepted five-spearman print does
not establish physical acceptance of these revised faces.
