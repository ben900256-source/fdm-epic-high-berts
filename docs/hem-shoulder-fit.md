# Hem and shoulder fit

Changes requested using the standing-guard viewer IDs:

- `01EA`: all five mail-skirt trim variants now use revision 8. Their rear
  limit moves from local Y 0.50 to 1.10 mm. Cutouts use the current grounded
  cape revision 4, shifted 0.15 mm rearward to leave overlap into the cape.
- `0197`: skirt revision 8 removes 0.70 mm from the bottom of the tapered
  hem band. The upper boundary, radius and taper slope stay fixed. Mail
  links, skirt backing and its existing Exact operations are preserved.
- `01BE`: both tunic shoulder mounts on each of the five source figures
  now place the shoulder-pad center on the corresponding breastplate
  armhole landmark. The move is approximately 0.23–0.24 mm outward and
  0.05–0.12 mm upward, depending on the pose. Existing tunic geometry and
  arm poses are reused; inherited infantry variants receive the adjustment.

The saved visual review is `out/hem-shoulder-fit-review`. Geometry compiled
once for the six changed definitions; unchanged parts use their cached
collections. Saved Blender provenance passes and `EVALUATED_EXPORT` is empty.

The evaluated visual fit probe confirms that the lower band ends at world
Z 1.989–2.010 mm, above the soles at Z 1.925 mm. Trim vertices are embedded
into both sides of every cape. All ten shoe/trim pairs still have zero
crossing faces, with sampled surface clearances approximately 0.075 mm.
Resolver tests check all inherited shoulder/armhole centers.

This is visual-only. No slicing, manufacturing validation or physical trial
was performed. Earlier definitions and saved reviews are preserved.

Follow-up `01B6`: left-arm revision 4 removes the separate `left_forearm`
cylinder from the standing guard. All other arm atoms and the assembly mount
are preserved. The evaluated vambrace still overlaps the elbow transition
and cuff. The current follow-up review is `out/shield-arm-no-cylinder-review`;
only this arm was compiled, and the assembled row reuses all cached parts.
