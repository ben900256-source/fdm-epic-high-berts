# Shield tip tucked into the mail hem

The five shield poses now add only 3 degrees of inward tilt to their original
poses and move 0.60 mm toward the body along the shield's local depth axis.
The shield outline and relief geometry are reused;
the insignia follows the same rigid transform. All shield-bearing workshop
models inherit these placements from `specs/elf-modular-visual.json`.

Lower connector revision 6 replaces the round cone with a flat backing cut
from a box using ordered Exact intersections. Its sides narrow behind the
shield point; the underside rises from inside the mail hem. The embedded
body is 1.0 mm wide. The cached join is now placed 0.10 mm farther back along
the shield's depth axis, leaving its front about 0.095 mm behind the shield
face. The complete bottom edge of the bevelled tip remains embedded in the
backing; the previous 0.20 mm setback left its front edge exposed. The shield
pose stays unchanged, and no ground-contact foot is added.

The recipe is `fdm_sculpt/components/shield_tuck.py`. Recreate the pinned
definitions and placements with:

```powershell
py -3.13 scripts/generate-shield-tuck.py --seed 1001
```

The source references, original mounts and chosen grip pivots are recorded in
`specs/shield-tuck-sources.json`. Revisions 3–5 and their source manifests
remain available as earlier fit studies. The generator always uses the
pinned original mounts, so rerunning it does not accumulate shield rotation.

Saved reviews:

- `out/shield-hem-balanced-row-review`: five original shield poses.
- `out/shield-hem-balanced-review`: all ten spearman variants.

Atelier reopens the saved scenes to verify provenance. The background Blender
probe `tests/shield_tuck_scene_probe.py` checks shield-to-hand, shield-to-upper
connector, shield-to-lower-join and join-to-skirt contact, plus containment of
the complete bottom edge and rear vertices in the shield's lowest 0.10 mm
inside the concealed join, and clearance behind the shield's front face.

These are visual fit checks only. The joins are intended to address the
previous hanging shield tips; support-free printing has not been established.
Actual sliced layers, rim and insignia undersides, followed by a physical print
trial, remain to be checked during manufacturing preparation.
