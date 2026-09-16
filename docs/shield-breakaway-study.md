# Shield breakaway support study

**Parked at the user's request.** The current row now uses shield revision 2
without a ground-contact foot or removable pedestal. The saved trials below
are historical candidates for a later review; do not repin or publish them as
the current design.

This is a separate visual prototype requested by the user, not a print-ready
support. Review the archived comparison in the
local viewer under **Shield breakaway trials - 0.30 / 0.40 / 0.50 mm**.

The proposed design is a short sacrificial pedestal beneath the shield point,
with narrow necks above and below its body. The recessed necks give flush cutters
an approach from the front of the miniature. Clip the upper neck while holding
the pedestal, then clip the lower neck at the base. Do not use the shield as a
lever. The model's existing arm and shield connectors remain permanent.

The recommendation to try clipping rather than twisting is an engineering
judgment for this very small shield. Prusa notes that removing supports from
miniatures can damage delicate features; it does not prescribe these neck sizes.
[Prusa's 0.25 mm miniature guide](https://blog.prusa3d.com/printing-great-looking-miniatures-with-a-0-25mm-nozzle-on-the-original-prusa-mini_33457/)

| Front-view position | Design | Purpose |
| --- | --- | --- |
| 1, left | 0.30 mm neck depth | Small-contact candidate; greatest risk of missing extrusion |
| 2 | 0.40 mm neck depth | Middle candidate to try first |
| 3 | 0.50 mm neck depth | Stronger candidate; potentially harder removal |
| 4 | Original shield without a pedestal | Shape control |
| 5, right | Former permanent foot | Historical-design control |

All three candidates have 0.55 mm wide necks, a 0.70 x 0.85 mm body and a
0.80 x 0.85 mm foot. The complete support spans shield-local Z -3.34 to -2.10 mm;
its upper neck deliberately overlaps the shield point. The foot is embedded in
the current base. The visible neck length depends on the shield tilt and terrain.
The components share each shield's rigid mount, so the test also exposes pose
and removal-access differences. For physical calibration, compare all three
necks on the same pose before attributing differences to neck size.

These are attached sacrificial connections with **no air gap**. Their behavior
differs from slicer-generated supports. If the necks fuse too strongly or the
tool cannot reach them, the next candidate should be a local support enforcer
under the point, with snug rectilinear support and a tested contact gap.
Prusa documents that snug supports follow the overhang closely, rectilinear
patterns are generally easier to remove, and contact separation controls the
tradeoff between release and the supported surface.
[Prusa support settings](https://help.prusa3d.com/article/support-material_1698)

No nominal neck size is established as printable or safely breakable. Before
printing a full row, slice a small comparison using the pinned XL tool-2
0.25 mm PLA setup and inspect both necks, the first shield contours, any widening
by Arachne and the surrounding removal access. Then physically compare support
survival, cutting force, shield damage and residual marks. The prototype needs
these trials before replacing the permanent foot. It has not been sliced or
physically tested in this visual iteration.

Regenerate definitions and the pinned comparison with:

```powershell
py -3.13 scripts/generate-shield-breakaway.py --seed 1001
py -3.13 -m fdm_sculpt.atelier compose specs/elf-shield-breakaway-study.json --seed 1001 --output out/shield-breakaway-new-review
```
