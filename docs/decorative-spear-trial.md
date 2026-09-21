# Decorative faceted spearhead

The latest follow-up, `aurelian.uniform-spear-140-trial@3`, makes the blade
**15% thicker front-to-back** at the user's request. Its printed shoulder
thickness increases from 1.56 to **1.794 mm**. Width, length, shaft, collar,
grips and placements remain unchanged. Both blade sections thicken about their
common center plane, retaining the diamond cross-section and central ridge.

Use `specs/experiments/fuller-spear-infantry-{1..5}-trial.json` for this version;
generate with `py -3.13 scripts/generate-fuller-spear-trial.py`.
[Updated comparison](http://127.0.0.1:8765/?review=fuller-spear-infantry-comparison-trial)
and [gallery](http://127.0.0.1:8765/?review=fuller-spear-infantry-gallery-trial)
are in `out/fuller-spear-20260921/`. Golden/resolver checks pass for both revisions.
This remains visual-only and awaits sliced and physical print checks.

## Original decorative revision

The user found the short spearhead read as a nub at tabletop distance. This
2026-09-21 visual trial replaces it with a broader, longer leaf-shaped blade.
Four-sided sections form a diamond cross-section and a central ridge on both
faces, giving the head a clear silhouette and broad light-catching facets.

At the existing 130% print scale:

- Maximum blade width: **3.12 mm**.
- Blade length from its embedded root: **4.641 mm**.
- Blade thickness at the widest shoulder: **1.56 mm**.
- Terminal cap: **0.702 × 0.351 mm**, with measured minimum planar caliper
  **0.314 mm**. This is a small flat end, not an infinitely sharp point.
- Uniform shaft: **1.82 mm**, unchanged from the previous trial.

The lower blade flares gradually from inside the collar, then narrows along a
long upper taper. The new terminal is 2.535 mm farther along the spear axis than
the previous one; the shaft length, axis, collar and hand remain unchanged.
The 0.314 mm cap follows the provisional terminal-tip target, not a proven
printable minimum. Tiny terminal layers still require sliced and physical review.

New part: `aurelian.uniform-spear-140-trial@2`. It uses primitive frusta and
ordered local Exact unions into the shaft, producing one connected local mesh.
All five latest infantry poses use the new part; other geometry and mounts are
unchanged. Previous part definitions and assembly reviews remain available.

- [Gallery](http://127.0.0.1:8765/?review=decorative-spear-infantry-gallery-trial)
- [Before/after comparison](http://127.0.0.1:8765/?review=decorative-spear-infantry-comparison-trial)
- Recipes: `specs/experiments/decorative-spear-infantry-{1..5}-trial.json`
- Generator: `py -3.13 scripts/generate-decorative-spear-trial.py`

Only the changed spear was compiled. Isolated and assembled provenance checks
passed; all other components were loaded from immutable caches. Golden/resolver
tests confirm the uniform shaft, collar, hands and other placements are unchanged.
Evaluated geometry confirms blade and cap dimensions, one local connected
component and 1.82 mm shaft sections above and below the hand. The previous
hand, sleeve, shoulder-fill and footing attachment intersections remain positive
in every pose. Viewer checks include front/side views, full figures and close
blade views, with the loaded revisions checked against the published index.

Evidence: `out/decorative-spear-20260921/`, including
`attachment-and-shaft-check.json`, viewer captures and saved provenance.
This is visual-only, with no new print export or slicing. It does not establish
support-free printing, terminal strength or physical tabletop readability.
The separate three-mini cooling comparison retains its original geometry.
