# Flush helmet nape

The current spearman assembly pins `aurelian.helmet@7` and `aurelian.torso@4`.
The lower transition is part of the helmet, so it follows the head rotation.
The torso's separate revision-3 collar flare has been removed.

A parameterized elliptical primitive meets the original crown at local
Z -0.55 mm with matching radius and tangent. The transition ends at Z -1.40 mm,
inside the collar region. The upper crown, pointed cap and original face-opening
primitive are preserved. A lower clearance continues the face opening below
its original limit. All operations are local Exact CSG; there are no hand-edited
vertices. The saved sources retain every primitive and operation.

Revision 6 is a rejected intermediate preview: its many nearly coincident
frusta produced a face-cut artifact. Keep it for provenance, but use revision 7.
The current recipe uses one elliptical primitive and includes an exported-view
regression check against the artifact.

Saved reviews:

- `out/helmet-flush-nape-v7`: isolated part and side-view screenshot.
- `out/spearman-flush-helmet-v7-review`: current row, saved provenance,
  viewer manifest and front/back/side screenshots.
- `out/shield-breakaway-review-v1`: separate support comparison with this helmet.

The subsequent placement adjustment turns `aurelian.left-arm@3` outward by
8 degrees about its upper-arm shoulder endpoint, in the arm's local Y axis.
It changes the `elf-01/left-arm` mount only and reuses the immutable arm cache.
The current row is saved in `out/spearman-helmet-arm-review`; the corresponding
support comparison is `out/shield-breakaway-arm-review`.

The final cape correction pins all five `aurelian.cape*@4` variants. Their
original hems were at Z 1.425 mm, 0.50 mm below the soles and below the base
surface. Revision 3 raised them to Z 2.775 mm, but the user requested ground
contact. Revision 4 shortens the original bottom by 0.575 mm while preserving
the upper endpoint, shoulder drapes and taper slope. Its hems end at Z 2.0 mm,
the base's top plane, with deliberate contact into the terrain relief.

The user subsequently deferred shield supports. The current row uses shield
revision 2, with neither the permanent ground-contact foot nor a removable
pedestal. The final combined review is `out/spearman-grounded-capes-review`.
Earlier support comparisons remain saved historical studies.

These are visual-only revisions. Earlier overhang-study slice statistics do
not validate this changed nape. Its lower curve needs another deposited-layer
assessment when print preparation resumes, especially where it emerges from
the collar on turned heads. No slicing or physical trial was performed here.

```powershell
py -3.13 scripts/generate-helmet-nape.py --seed 1001
py -3.13 -m fdm_sculpt.atelier part aurelian.helmet@7 --seed 1001 --output out/helmet-new-review
py -3.13 -m fdm_sculpt.atelier compose specs/elf-modular-visual.json --seed 1001 --output out/helmet-row-new-review
```

See the separate [shield support study](locked-spearmen.md) for the
removable pedestal candidates.
