# Uniform spear and fuller gripping hand

The user requested a uniform shaft regardless of the chosen thickness, allowing
an oversized hand to make the grip read convincingly. This 2026-09-21 visual
trial uses **1.82 mm diameter at print scale throughout the shaft**. It replaces
the previous 1.56 mm lower / 2.08 mm upper split and removes its transition above
the hand. The source diameter is 1.40 mm; apply the existing 1.3 print scale once.

The palm, grouped fingers, thumb and knuckle plate grow 25% in each dimension
about their existing centers. Additive wrist tapers grow at their hand ends;
their wrist roots, sleeve geometry, shoulders and pose mounts remain fixed.
The lower finger transition broadens 20% at its hand end. The spearhead and
collar radii shrink by 12.5% to match the slimmer upper shaft. The decorative
collar remains a separate detail immediately below the spearhead.

The shaft is one 64-sided cylinder from local Z=-6.15 to 7.20 mm, centered at
X=0, Y=0.46. Its original axis, bottom, top and overall weapon length are retained.
Its butt has the existing small edge bevel. The current clearer face, opened
helmet, raised flat seahorse, enlarged sleeves and shoulder/helmet fill remain.

- Spear: `aurelian.uniform-spear-140-trial@1`.
- Hands: `aurelian.open-right-arm-{1..5}-trial@2`.
- Figure recipes: `specs/experiments/uniform-spear-infantry-{1..5}-trial.json`.
- Generator: `py -3.13 scripts/generate-uniform-spear-trial.py`.
- [Five-pose gallery](http://127.0.0.1:8765/?review=uniform-spear-infantry-gallery-trial).
- [Before/after comparison](http://127.0.0.1:8765/?review=uniform-spear-infantry-comparison-trial).

Only the six changed components were compiled; all other caches were reused.
Isolated spear/pose-3 arm and assembled gallery/comparison provenance checks
passed. Golden-hash/resolver tests verify unchanged mounts, sleeves, wrist
landmarks, other components and shaft endpoints.

Evaluated cross-sections at source Z=-5, -2, 0, 2 and 5 mm all measure 1.82 mm
diameter at print scale. Local Exact intersection checks confirm positive overlap
for palm/fingers/thumb to shaft, palm to sleeve/fingers, thumb/knuckles to fingers,
and shaft to shoulder fill and footing in all five poses. The smallest checked
shaft/footing overlap is 0.075 mm³ in pose 4. These are attachment checks, not a
strength guarantee. Viewer checks cover front and side views for every pose and
close grip views, verifying the loaded revision against the published index.

Evidence: `out/uniform-spear-20260921/`, including
`attachment-and-shaft-check.json`, `viewer-check.json` and saved provenance.
This remains visual-only; no new print export or slicing was performed. Larger
hands retain unvalidated finger undersides. The existing three-mini cooling
experiment keeps its original mesh; use these recipes for a subsequent geometry
trial after choosing the cooling settings.
