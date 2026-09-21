# Clearer face and helmet opening

The 2026-09-21 visual trial gives the latest raised-flat-shield infantry a
broader face and stronger recesses. It preserves head mounts, pose angles,
the helmet's outer crown/nape/tip, the nose and its underside treatment.

| Feature | Previous source dimensions (mm) | New source dimensions (mm) |
| --- | --- | --- |
| Cranium width | 1.44 | 1.584 (+10%) |
| Helmet face opening, width × height | 1.08 × 1.74 | 1.20 × 1.86 |
| Eye cutter, width × depth × height | 0.52 × 0.76 × 0.30 | 0.62 × 0.88 × 0.36 |
| Mouth cutter, width × depth × height | 0.72 × 0.50 × 0.24 | 0.82 × 0.62 × 0.28 |

At 130% print scale the cranium is 2.059 mm wide, the helmet opening is
1.56 × 2.418 mm, and the eye/mouth cutter heights are 0.468 / 0.364 mm.
These are primitive dimensions; surface apertures depend on the evaluated CSG.
The eyes move outward from ±0.30 to ±0.34 mm; the chin and head envelope widen
with the cranium. The cheek hollows move outward to retain the fuller face.
The mouth cutter moves inward 0.02 mm. The helmet opening bevel decreases from
0.12 to 0.08 mm, making its border more distinct.

New parts are `aurelian.readable-head-trial@3` and
`aurelian.readable-helmet-trial@1`. All other parts, including the raised flat
seahorse, are reused. Earlier definitions and reviews remain available.

- [Five-pose gallery](http://127.0.0.1:8765/?review=clear-face-infantry-gallery-trial)
- [Before/after comparison](http://127.0.0.1:8765/?review=clear-face-infantry-comparison-trial)
- Figure recipes: `specs/experiments/clear-face-infantry-{1..5}-trial.json`
- Generator: `py -3.13 scripts/generate-clear-face-trial.py`
- Local review evidence: `out/clear-face-20260921/`

Both new parts compiled once; assemblies reuse immutable caches. Isolated and
assembled saved-scene provenance passed. Golden/resolver tests confirm pinned
revisions, unchanged other placements, helmet outer primitives and nose geometry.
Evaluated Exact intersections remain positive in every pose for head-to-helmet,
head-to-body joins, head-to-shoulder fill and helmet-to-shoulder fill. Rays at the
brow, temples, eyes and mouth hit filled head geometry; eye floors are at local
Y=-0.38 and the mouth floor at Y=-0.51 mm. Viewer revision checks and front/side
reviews cover the current composition.

This remains visual-only. Larger recessed ceilings still need sliced-detail and
physical testing; these geometry checks do not establish support-free printing.
The three-mini cooling experiment retains its previous mesh to preserve that
controlled comparison. Use these new figure recipes for a subsequent geometry
test after choosing the cooling settings.
