# Cloth arms, capes and archer robes

Spearmen and archers now use complete posed cloth arms. Each of the 32 arm
poses has an independently versioned recipe: a small fitted shoulder, fuller
elbow, tapered forearm and broad fabric folds. The new cloth volume replaces
the old upper-arm rods, joint shapes and vambraces. Separate spearman tunic
sleeve overlays have been removed. All hand primitives, grip landmarks and
assembly mounts are retained, including horn, sword and hawk command poses.

The current elbow revisions keep those sleeve shapes and their original round
elbow cores. Three shallow curved creases and two low gathers across the outer
elbow continue the cloth texture through the bend. The hanging drape experiment
was undone; it is not part of the current models.

Four forward/elevated archer bow-arm revisions include an inset cloth yoke
to close the gap between the narrow shoulder and the sideways robe body.
These revisions preserve the initial cloth-arm studies and their golden hashes.
Spearmen retain their mail skirt at revision 8, breastplate, skirt edging
and reviewed shoes.

All five cape variants use revision 5. Six broad folds and recessed valleys
run down the back. The original cape primitive, grounded hem, shoulder drapes
and front surface meeting the skirt edging are preserved.

Archers use tunic revision 5, with fuller skirt folds and diagonal chest
gathers above the belt. Their robe length, belt, collar and poses are retained.
Swordmasters explicitly pin their previous shoulder pieces, cape and mail
skirt so their armored appearance does not inherit these changes.

Current visual reviews:

- `out/spearmen-elbows-socket-review`
- `out/spearmen-command-elbows-socket-review`
- `out/bearer-cloth-elbows-review`
- `out/archers-cloth-elbows-review`
- `out/archer-sergeant-cloth-elbows-review`

Recreate the arm definitions and model pins with
`py -3.13 scripts/generate-robe-arms.py --seed 1001`.
Apply the elbow detail with `py -3.13 scripts/generate-robe-elbows.py --seed 1001`.
The source pose references and hashes are pinned in `specs/robe-arm-sources.json`.
Elbow texture sources and new versions are pinned in `specs/robe-elbow-sources.json`.
The generator preserves immutable definitions and checks existing golden hashes.
Compile isolated arms with `atelier part`, then compose the relevant gallery;
unchanged cached parts are reused.

Earlier separate sleeve revisions, lowered shoulder studies and the unused
cloth-skirt revision 9 are preserved for reference. The old sleeve placement
script applies only to those historical overlay assemblies.

Golden and resolver checks cover the recipes, exact hand geometry, grip
landmarks and family pins. Atelier checks saved Blender provenance.
`tests/robe_arm_contact_scene_probe.py` checks the evaluated sleeve surfaces
against hands and bodies for visual contact. These are visual-only reviews;
no slicing, manufacturing validation or physical print trial was performed.

Spear revision 5 also shortens the hidden shaft top by 0.40 mm so it ends
inside the collar instead of breaking through the narrow lower blade.
The collar, both blade shapes, bottom and total spear height are unchanged.
Recreate it with `scripts/generate-spear-socket-cleanup.py --seed 1001`.

Horn arm revision 11 removes the oversized palm sphere identified as #16CD.
The unchanged thumb overlaps the sleeve and grouped fingers, and both remaining
hand pieces contact the horn. The cloth sleeve and elbow texture are retained.
Recreate it with `scripts/generate-horn-palm-cleanup.py --seed 1001`.
The visual review is saved in `out/bearer-palm-cleanup-review`.
