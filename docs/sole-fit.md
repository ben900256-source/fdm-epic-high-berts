# Close-fitting boot soles

The current boot revisions shorten only the front of each sole, targeting a
0.04 mm rim beyond the toe upper. Spearman and swordmaster legs use revision 6;
archers use the narrower original boot shape with revision 7. Heel positions,
toe uppers, sole width and thickness, stance and skirt-clearance cuts are preserved.

`specs/sole-fit-sources.json` pins the original definitions and seed. Recreate
the immutable revisions and update the live model references with:

```powershell
py -3.13 scripts/generate-sole-fit.py --seed 1001
```

The evaluated visual surfaces retain approximately 0.040–0.047 mm of front rim.
All 46 boots in the spearman and archer variant galleries retain sole-to-toe
contact. `tests/sole_fit_scene_probe.py` records these measurements from cached
geometry in its posed foot frame.

Saved reviews: `out/trimmed-sole-part-review`,
`out/aligned-hands-trimmed-soles-spearmen`,
`out/aligned-hands-trimmed-soles-archers`, and
`out/aligned-hands-trimmed-soles-row`. These are visual-only assemblies, with
saved-scene provenance checks; no manufacturing build or slicing was performed.
