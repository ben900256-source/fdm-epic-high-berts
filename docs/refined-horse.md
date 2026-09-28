# Refined cavalry horse

The current cavalry recipe, [`specs/elf-dragon-prince.json`](../specs/elf-dragon-prince.json),
uses **horse revision 7** and **barding revision 10**. This is a visual-only update;
it has not been sliced or physically printed.

The horse now has tapered limbs with buried shoulder/hip roots, a sloping face,
recessed eyes and nostrils, closed lips, rounded ears with inset hollows, and a
continuous mane and swept tail with shallow hair channels. Higher-resolution
primitives reduce visible faceting. Left/right forefeet are staggered by 0.60 mm
and hindfeet by 0.56 mm in source coordinates; all four hooves remain on the same
ground plane and within the original cavalry base. Lower-leg stations retain at
least 0.86 mm source diameter (1.118 mm after the existing 1.3 export scale).
These are recipe dimensions, not evaluated printability claims.

The saddle position, rider, equipment mounts, base and export scale are unchanged.
The scalp cap, forehead plate and nose armor are fitted to the new head. Reins
retain their existing geometry and intended bit/hand contacts. The visual rein
checker now derives the fist contact region from the saved fist primitive and
includes rein radius; its former fixed centerline box incorrectly rejected the
start of legitimate contact with the enlarged fist. Clearance checks away from
those intended contacts retain their previous thresholds.

The recipes live in [`refined_horse.py`](../fdm_sculpt/components/refined_horse.py).
Reviewed intermediate revisions 6 and 9 remain immutable alongside final
revisions 7 and 10. The accepted-army generator pins the new horse and armor,
so regenerating the army does not restore the old mount. Locked spearmen remain
unchanged.

Visual review used the local Three.js viewer, with the horse bare, tacked and
assembled, including front, side, rear, overhead and three-quarter views.
Saved Blender provenance and component definition hashes pass. The final
assembly reuses 16 cached parts; only the revised barding needed compiling there,
with the horse already compiled and reviewed in isolation. No full-strip fusion,
mesh printability gate, independent geometry repeat, rendering or slicing was run.

See [the recorded checks](evidence/refined-horse-visual-20260928.json).

Viewer: [assembled cavalry](http://127.0.0.1:8765/?review=aurelian-dragon-prince)
or [isolated horse](http://127.0.0.1:8765/?review=isolated-aurelian.dragon-prince-horse).
