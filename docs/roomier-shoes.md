# Roomier shoes and piece identification

The current assembly pins all ten left/right leg variants at revision 5.
Soles grow from 0.91 x 1.90 mm to 1.12 x 2.35 mm; shoe uppers grow from
0.88 x 1.63 mm to 1.08 x 2.04 mm. Heel positions, sole bottoms, leg geometry
and assembly mounts stay fixed. The extra length projects toward the toes.

The upper is slightly lower, with local Exact recesses around an expanded
skirt-trim envelope and front band. The shoe part owns these hidden operands
and records the trim revision and definition hash. The skirt itself is unchanged.
This avoids the upper protruding through the edging while retaining the ankle
connection inside the garment.

`out/spearman-roomier-shoes-review` contains the saved visual scene and
`shoe-trim-fit.json`. The visual fit probe finds no crossing shoe/trim faces
in any of the ten feet; sampled surface clearances are about 0.075-0.078 mm.
That small visual separation is not a printable-gap claim. No slicing or
physical trial was performed.

```powershell
py -3.13 scripts/generate-roomier-shoes.py --seed 1001
py -3.13 -m fdm_sculpt.atelier part aurelian.left-leg@5 --seed 1001 --output out/shoe-isolated-new
py -3.13 -m fdm_sculpt.atelier compose specs/elf-spearmen-overhang-study.json --seed 1001 --output out/shoes-new-review
```

The viewer now exports triangle ranges for each visible geometry role. Hold
**Ctrl while hovering** to outline the individual piece and show its name
together with the component name and revision. The exact piece is orange;
the rest of its component is yellow. Both outlines show through geometry that
occludes the selected surfaces. Alt-hover is an alias.
Fused surfaces retain their final output role
(for example, the shoe upper includes its instep and ankle). Hidden Boolean
cutters are not selectable. Old saved exports use the component-level fallback
until republished. Alt+Tab keeps its normal Windows behavior and clears the
hover highlight.
