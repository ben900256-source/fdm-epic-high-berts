# Hands aligned with held equipment

The hand-only revisions rotate palms, grouped fingers, thumbs and attached
hand details together. The fingers' grip axis follows the held spear, sword,
bow handle, extracted arrow or local horn curve. Shield hands also follow the
shield plane. Existing sleeves, elbow texture and equipment placements remain
unchanged. Each hand rotates about its existing palm/grip centre.

The audit covers the workshop's equipment-holding hands across all infantry
families. Already aligned poses, including greatswords and elevated archery,
retain their existing definitions. Empty hands and the perched-hawk glove
retain their reviewed poses. Arrow-drawing hands follow the bowstring's overall
axis rather than turning along the nocked arrow.

`specs/hand-alignment-sources.json` pins source definitions, rotations, pivots
and model-specific placements. Shared arms get distinct revisions where the
same sleeve holds items at different angles. Recreate them with:

```powershell
py -3.13 scripts/generate-hand-alignment.py --seed 1001
```

Reviews are saved under `out/aligned-spearman-hands-review`,
`out/aligned-archer-hands-review`, `out/aligned-bearer-hands-review` and
`out/aligned-horn-sergeant-hands-review`. The background Blender probe
`tests/hand_alignment_scene_probe.py` checks each changed hand against its
sleeve and held item using the cached posed surfaces.

These are visual-only reviews, with saved-scene provenance checks. No slicing,
manufacturing validation or physical print trial was performed.
