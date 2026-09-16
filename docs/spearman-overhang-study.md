# Spearman underside design study

This records the historical sliced study. The [current design](helmet-flush-nape.md)
subsequently changed the helmet, arm placement and cape hems, and removed the
shield feet. The slice results below do not validate those later changes.

This implements the changes identified in the CLI review of the five mixed
spearmen: standing guard, watching left, watching right, spear forward and
spear outward. Seed 1001, a solid 20 x 5 x 2 mm base, and the original poses
are retained. The master assembly is `specs/elf-modular-visual.json`; the
reproducible comparison layout is `specs/elf-spearmen-overhang-study.json`.

## Revised geometry

| Parts | Change |
| --- | --- |
| Torso @3 | A rear collar ramp grows underneath the helmet nape while leaving the face clear. |
| Skirt @7 | A terrain-embedded lower taper reaches the full width of the separate decorative hem. |
| Right arms @3, including b-e | Tapers join the elbow, palm and grouped fingers beneath the spear grip. |
| Right tunic @3 | A tapered underside connects the pauldron hem to the arm. |
| Spear @4 | A longer socket ramp and matching blade depth remove the abrupt widening between the two blade sections. The shaft, grip and terminal tip remain unchanged. |
| Shield @5 | A permanent tapered shoe extends the lower point into the terrain, with a wider root to retain deposited paths. |
| Shield lower/torso connectors @2, including b-e | Lower diagonal joins back the existing horizontal struts. |
| Shield insignia @4 | Shallow tapered backing supports the lower edges of the relief strokes. |

The face @12, helmet @5 and crest @4 retain their reviewed definitions.
No poses or assembly transforms changed. The new features are permanent
model geometry, not removable support material. The shield's lower outline
and the skirt's underside now extend toward the terrain; inspect these in
the viewer before accepting their appearance.

Recipes live in `fdm_sculpt/components/spearman_overhangs.py`. Each saved
revision has a golden definition hash. Earlier definitions, initial studies
and their saved scenes remain available. Component generation uses only
parameterized primitives and the preserved local Exact operation sequences.

```powershell
py -3.13 scripts/generate-spearman-overhangs.py --seed 1001
py -3.13 -m fdm_sculpt.atelier compose specs/elf-spearmen-overhang-study.json --seed 1001 --output out/spearman-overhang-review-new
```

The historical generator repins the original underside-study parts, including
shield feet. Do not run it to restore the current design; use its saved review
for comparison and the current design notes for the later recipes.

Only missing parts compile; a composition of the final cached revisions
reuses all 57 assets. The saved visual scene has an empty `EVALUATED_EXPORT`
and passes the reopened-scene provenance checks. Select **Spearmen - tapered
underside study** in the local viewer's saved reviews.

## Sliced evidence

The diagnostic uses PrusaSlicer 2.9.5 CLI with the same saved stock
`0.05mm ULTRADETAIL @XL 0.25` settings as the baseline: tool 2, 0.25 mm
nozzle, 0.05 mm layers, 0.20 mm first layer, supports off and no brim.
The nozzle array remains `0.4,0.25,0.4,0.4,0.4`. Installed presets are
unchanged. Each saved project is reopened and sliced without a separate
configuration file.

The comparison uses the shared deposited-toolpath screen with its original
thresholds and a raster enclosing the complete row. Historical `regiment
assess` requires the separate 0.14 mm-first-layer proof profile; those gates
are unchanged. Diagnostic STL geometry uses the authorized Blender Manifold
union and native STL export, without mesh validation or repeat geometry builds.

These remain **visual-only design revisions with separate sliced diagnostics**.
The STL is **unchecked Blender output**. No physical trial or digital print
validation is claimed. Run counts are repeated layer events, not independent
defects; nearest-component attribution is approximate near joins. Internal
infill flags must be distinguished from exterior undersides.

## Results, seed 1001

Final review: `out/spearman-overhang-review-v4`, viewer revision
`d27a98c3a4e68547e92e5727b982cb48daf0502834156ea6ffc7bd383dc65d57`.
Final slice: `out/spearman-overhang-trial-v4`. Its `README.md`,
`comparison.json`, `overhang-report.json`, `slice-evidence.json` and
`previews/printability.json` retain the numeric comparison and provenance.

| Unchanged deposited-path screen | Baseline | Revised |
| --- | ---: | ---: |
| All flagged runs, including internal fill | 239 | 162 |
| Runs involving any perimeter | 140 | 92 |
| Flagged perimeter path length | 84.337 mm | 25.882 mm |
| Runs involving exterior/overhang perimeters | 81 | 30 |
| Longest flagged exterior path | 3.427 mm | 0.440 mm |

Flagged perimeter path length falls **69.3%**. The two normalized slicer
configurations compare equal. All 105 instance IDs and placement matrices
match the baseline. The shaft, tip and approved head/helmet definitions
remain preserved. Resolver/golden regression checks and the final saved-scene
provenance checks pass; the viewer loads the recorded revision without errors.

The remaining 30 exterior/overhang runs are attributed approximately to:

| Location | Runs | Height above bed (mm) |
| --- | ---: | --- |
| Small mail-skirt details | 16 | 4.55-5.90 |
| Shield lower edges and lower connector | 5 | 2.90-3.00 |
| Hem trim | 3 | 2.30-2.75 |
| Left and right arm details | 3 | 5.90-7.20 |
| Terrain detail | 1 | 2.15 |
| Tiny head/helmet starts | 2 | 8.55 and 11.60 |

Other remaining flags involve inner perimeters and infill. They are not
silently accepted: the conservative screen still fails. This study implements
the proposed underside changes and substantially reduces the major overhangs;
it does not establish a support-free print or fine-detail survival.
