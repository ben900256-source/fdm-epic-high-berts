# Flat seahorse shield trial

On 2026-09-22 the user accepted the [wider-shield print](wider-shield-trial.md)
and explicitly chose the more raised insignia. Keep revision 4 as the default;
revision 3 remains the historical shallow comparison.

The current follow-up is `aurelian.readable-insignia-trial@4`: the user approved
the flat outline and requested more raise. Its relief is **0.39 mm at print
scale**, 50% higher than revision 3. The silhouette, bevels, 0.156 mm embedded
back and all figure placements remain unchanged. Evaluated depth and shield
overlap were checked; both revision/resolver tests and saved-scene provenance pass.

The original raised-emblem trial is in
`specs/experiments/raised-flat-seahorse-infantry-{1..5}-trial.json`.
Generate it with `py -3.13 scripts/generate-raised-flat-seahorse.py`.
The [raised gallery](http://127.0.0.1:8765/?review=raised-flat-seahorse-infantry-gallery-trial)
and [low / raised comparison](http://127.0.0.1:8765/?review=raised-flat-seahorse-infantry-comparison-trial)
are published from `out/raised-flat-seahorse-20260920/`. This remains visual-only.

## Original flat revision

The 2026-09-20 revision replaces the projecting seahorse and its underside ribs
with a broad, flat silhouette. It uses the current fuller-arm infantry, preserving
every other part and all mounts. Earlier reviews remain available.

- Part: `aurelian.readable-insignia-trial@3`.
- Five figure recipes: `specs/experiments/flat-seahorse-infantry-{1..5}-trial.json`.
- [Gallery](http://127.0.0.1:8765/?review=flat-seahorse-infantry-gallery-trial).
- [Before/after comparison](http://127.0.0.1:8765/?review=flat-seahorse-infantry-comparison-trial).
- Generator: `py -3.13 scripts/generate-flat-seahorse.py`.

The outline retains the head, snout, crest, belly and curled tail. Elliptical
cylinders with small edge bevels replace the rounded projecting strokes;
ordered Exact unions form one planar emblem. The source stroke width is at
least 0.48 mm (0.624 mm at 130% scale, before edge bevels). No underside ribs remain.

The shield front is at local Y=-0.52 mm. The emblem occupies Y=-0.72 to -0.40 mm:
0.20 mm raised and 0.12 mm embedded at source scale, or **0.26 mm raised and
0.156 mm embedded** at print scale. Evaluated geometry matches these dimensions;
its Exact intersection with the shield is 0.731 mm³ at print scale. All five
figures use the same shield/emblem relationship.

Only the new emblem was compiled. All unchanged component caches were reused.
The isolated part, gallery and comparison passed saved-Blender provenance checks.
Golden-hash/resolver tests confirm immutable definitions, pinned assemblies and
unchanged other parts and placements. Viewer review includes front, side and
overhead views, with loaded revisions checked against the published index.

Local evidence is in `out/flat-seahorse-20260920/`, including
`flat-relief-check.json`, saved reviews and viewer captures. This is visual-only:
no new manufacturing export, slicing or physical print validation was performed.
Use the accepted wider-shield figure recipes for current infantry work; they
retain the raised emblem with the later face, weapon and shield improvements.
