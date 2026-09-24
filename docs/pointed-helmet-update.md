# Higher crests and restored pointed helmets

The current visual army uses conical helmet revision 5 and crest revision 7.
The five spearmen were subsequently printed and accepted on 2026-09-23;
see the [locked baseline](locked-spearmen.md). Other army variants remain
visual-only. The original verification record below predates that user trial.
The preceding height change enlarged the dome while leaving the upper join
too low. The five-pose default also bypassed the crest replacement and still
referenced revision 4. Both issues are corrected.

The upper shell and tip now form a continuous taper. The nominal top is
3.16 mm above the local helmet mount, retaining the intended 20% increase
over the earlier 3.8 mm helmet height. A small 0.24 mm source terminal flat
(0.312 mm at print scale, before bevel) retains the pointed appearance.
This terminal dimension remains a provisional design choice.

The triangular front crest is 35% broader at its outline, stretches upward
with the helmet, and rises another 0.16 mm in source coordinates. Its raised
spine overlaps the leaf backing. The default five-pose row and other current
models now all resolve the same crest revision.
The leaf has solid backing that extends into the helmet, closing the gap
found by the local contact probes in the earlier raised-crest study.

Evaluated geometry at the 1.3 print scale measures 5.928 mm in helmet height
versus 4.940 mm before the height experiments: exactly the intended 20%
increase. The crest measures 1.568 mm wide and 2.644 mm high, versus 1.159
and 1.787 mm in revision 4. Section probes through the crown-to-tip join
confirm a continuous narrowing profile.

The corrected three conical helmet families preserve their pre-stretch face
openings, napes and ornaments. The cavalry's separate helmet design is reused.
Head seating, restored nose, shield-facing correction and seahorse design
remain as in the preceding iteration. All 64 current recipes retain their
assembly mounts and other component references.

Recipes are in `fdm_sculpt/components/pointed_helmets.py` and are applied by
`scripts/generate-accepted-army.py`. Earlier definitions and caches remain
available. Reviews use seed 1001 and source scale; the 1.3 export scale still
applies exactly once.

Review the actual published army ID:
[updated spearmen](http://127.0.0.1:8765/?review=aurelian-spearmen-organic-faces).
`elf-modular-visual` is a filename, not that review's ID.

These are visual-only models. Local profile/contact checks and saved-scene
provenance do not establish sliced or physical print validation.

The [verification record](evidence/pointed-helmets-visual-20260923.json) covers
36 passing focused tests, 15 published/provenance-checked layouts and 132
passing local contact probes. The separate five-pose row also passed its
20 head/helmet/crest/fill contact checks. Front and side close-ups were
reviewed for infantry, both officer helmet styles and elevated archers.
