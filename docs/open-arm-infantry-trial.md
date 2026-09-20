# Fuller arms opened away from the body

This visual trial follows the user's request for bigger arms farther from the
body. It retains the broader torso, active head/shield turns and bold detail of
the readable-infantry study, with the same figure height and glue-in footings.

At the accepted 1.3 print scale, sleeve diameters increase 25%, elbow centers
move 0.91 mm outward and hands move 0.65 mm outward on each side. Shoulder
attachment centers stay fixed. Shields and spears translate with their hands;
their sizes, grip alignment, elevations and directions are retained. Hands
retain their original dimensions and additive cuff tapers.

The sleeves are rebuilt from overlapping cones and ellipsoids with ordered
Exact CSG. A tapered lower cloth drape rises from inside the skirt beneath
each elbow. An ascending envelope clips the projecting elbow underside;
opening the pose does not rely on a floating rounded elbow.

New detail revisions respond to the preceding overhang findings:

- Head revision 2 clips the nose underside to a face-backed ascending taper.
- Mail revision 3 uses diamond-shaped eye recesses with pointed roofs.
- Insignia revision 2 uses longer underside ramps rooted into the shield.

Mail revision 2 is an unused failed compiler prototype; revision 3 removes
an unsupported cube argument. Previously saved reviews and definitions remain
available. Each pose also has a refitted shoulder/helmet/spear join.

Generate with `py -3.13 scripts/generate-open-arm-infantry.py`. Reviews live in
`out/open-arm-infantry-20260919/`; gallery and comparison assemblies are pinned
under `specs/experiments/open-arm-infantry-*-trial.json`.

This remains **visual-only**. Nominal dimensions and geometry screens do not
establish unsupported printability. These wider poses require renewed shared
base and neighboring-figure clearance checks before print preparation, even
though the glue footings themselves are unchanged.

## Review and remaining overhangs

Golden/resolver, fixed-foot/shoulder and hand/equipment displacement checks pass,
as does the accepted-target regression (three tests). Isolated detail reviews,
the gallery and comparison pass saved-Blender provenance checks. Their loaded
revisions were checked in the local Three.js viewer.

Local evaluated Exact intersections found positive overlap on all five poses
between each sleeve and torso, sleeve and palm, lower cloth drape and skirt,
palm and held equipment, spear and footing, and refitted fill and torso/head/
helmet/spear. Existing shield connectors also retain body contact. This checks
the named attachments; it is not a whole-model topology or strength assessment.

The same approximate exposed-surface overhang screen used on the prior trial
was repeated at print scale. Across five poses, flagged area with more than
0.25 mm vertical clearance below changed as follows:

| Region | Prior readable trial, mm² | Opened arms trial, mm² |
| --- | ---: | ---: |
| Mail | 10.551 | 3.933 |
| Insignia | 7.546 | 2.961 |
| Face | 1.027 | 0.987 |
| Right arm | 2.712 | 3.792 |
| Left arm | 0.208 | 1.218 |

The mail and insignia improve under this geometric screen, but the nose change
does not substantially reduce total facial flags; eye/mouth ceilings remain.
Moving the arms outward exposes more finger and sleeve undersides. These are
**unresolved support risks**, not a support-free result. The refitted upper
joins have no flags in this screen. Vertical ray clearance is not bridge span
and does not establish whether the slicer's deposited paths will be supported.

Evidence: `out/open-arm-infantry-20260919/attachment-check.json`,
`viewer-check.json`, and `out/open-arm-overhang-check-20260919/surface-screen.json`.
No new print files, slicing or physical validation were performed.
