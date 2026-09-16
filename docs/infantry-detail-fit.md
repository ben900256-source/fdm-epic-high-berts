# Infantry detail and fist underside review

The clipped-fist revisions below are historical. The current hands preserve
their original shapes and use [additive tapered undersides](forward-spearmen-and-additive-fists.md).
The sliced measurements below describe the earlier clipped geometry.

The September 16 revision addresses the hawk sergeant's lower helmet edge,
disappearing bird legs, feather tips, and both hands. The same fist treatment
is applied to the shared spearman and short-sword arm variants.

- `aurelian.sergeant-helmet@4` uses the exact revision 7 ordinary helmet
  crown, face opening and curved nape. Its swept feather bodies are 0.80 by
  0.85 mm before their taper. Horizontal Exact caps stop the narrowing ends
  at approximately 0.55 mm rather than allowing needle points.
- `aurelian.hunting-hawk@3` has 0.76 mm shanks, slightly larger feet and
  attached talons. Their roots extend into the falconry glove. The bird's
  body, head and placement are preserved.
- Fifteen arm revisions intersect the existing palms, fingers, thumbs and
  falconry glove with a rising cuff envelope. The envelope starts inside
  the cloth cuff, with a 0.35 mm radius and 0.85 mm lateral growth per
  millimetre of height. Upper grips, equipment alignment and sleeve geometry
  remain pinned to their reviewed definitions.

`scripts/generate-infantry-detail-fit.py --seed 1001` reconstructs the
definitions from `specs/infantry-detail-fit-sources.json`. Historical sources,
intermediate helmet revision 3 and both golden sets remain immutable.
The separate [shield trim correction](shield-tuck.md#trim-behind-the-shield)
is included in the same gallery.

## Review evidence

`out/infantry-detail-fit-v2-gallery` is the visual-only assembled review.
Its viewer revision is
`cf154fec7f18d8f229c9aa4db9e59f2bd8b28b05e03eda09c81699b04faeccb3`.
The atelier reopened the saved scene and verified its component provenance.
The preceding gallery has the same arms, trim and placements: its fit probes
confirmed all 20 hands contact sleeves and equipment, and all nine shields
retain their lower backing and clear the decorative trim at the front face.

Focused before/after slices used PrusaSlicer 2.9.5, the installed profile
snapshot, tool 2, a 0.25 mm nozzle and 0.05 mm layers (0.14 mm first layer).
Installed presets were not edited. The installed application was 2.9.6;
a portable 2.9.5 copy supplied the pinned diagnostic CLI. Inputs were
unchecked Blender Manifold unions of cached figures, not validated builds.

The files in `out/infantry-detail-slice-before` and
`out/infantry-detail-slice-after-v2` contain saved projects reopened and
sliced without a separate configuration. The comparison accounts for each
project's bed translation before relating toolpaths to component landmarks.

| Region | Before | After |
| --- | --- | --- |
| Hawk-leg center witnesses | Missing on eight of 18 sampled leg layers/witnesses | All 18 contain deposited material |
| Sergeant nape blue overhang paths | 1.512 mm | 0 mm |
| Sword-fist blue overhang paths | 0.109 mm | 0 mm |
| Hawk-glove blue overhang paths | 1.747 mm | 0.022 mm |
| Feather terminal layers | Narrow contours omitted | Deposited through final layers |

The initial revision 3 cap-only change still lost intermediate tip layers.
Revision 4 broadens the feather stock as well. The last deposited layers are
Z 10.84 and 10.79 mm for the two wings, versus mesh tops of 10.831 and
10.795 mm; this is within one 0.05 mm layer. The enlarged toolpath overlay is
`out/feather-sliced-layers-v2.png`. The residual glove segment is at Z 6.54 mm.

The additional `out/fists-02-03-*` and `out/fists-04-05-*` comparisons did not
reproduce blue fist segments in those particular poses with the pinned
profile, before or after the change. Their common lower hand tapers are
nevertheless applied consistently. These local checks do not establish
whole-model support-free printing or physical durability. Existing STL
downloads are snapshots; export a new row to obtain the revised parts.
