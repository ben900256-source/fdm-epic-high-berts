# Future PrusaSlicer print-test settings

**Current experiment (2026-09-21):** the user reports that the slow single-mini
test produced worse rings on the spear. Use the
[three-mini cooling trial](three-mini-cooling-trial.md) to compare three identical
copies, 40 mm apart, printed layer by layer, with 10 mm/s minimum speed and a
10-second slowdown threshold. These are project overrides on the presets below;
the installed presets remain unchanged. Temperature and flow changes are deferred.

On 2026-09-20 the user requested a new print/filament pair to improve tiny-layer
cooling, stringing and detail with the existing **0.25 mm nozzle**. These are
experimental copies of the presets selected in the 2026-09-19 clipboard screenshot.
The originals remain installed and unchanged. Use
[the settings record](../specs/prusa-print-test-settings.json) for new trials.

| Setting | Selection |
| --- | --- |
| PrusaSlicer | 2.9.6 |
| Print preset | 0.05mm ULTRADETAIL @XLIS 0.25 - Epic Cool Detail v1 |
| Printer preset | Original Prusa XL - 5T Input Shaper 0.25 nozzle |
| Tool 2 filament | Epic FDM PLA - Cool Detail v1 |
| Other tools' filament | Generic PLA @XLIS (shown as Generic PLA in the UI) |
| Supports | None |

The new **Epic FDM PLA - Cool Detail v1** profile specifies **205°C printing,
230°C first layer, and 60°C bed**. Use its saved temperatures, including the
first-layer value; the preceding spear experiment's 205°C first-layer override
is superseded. Read the installed presets when preparing each new trial, so
later saved user adjustments are respected. Do not edit installed presets.

Keep tool 2 assigned to the model and preserve the physical nozzle array
`0.4,0.25,0.4,0.4,0.4`. Continue the previously requested spaced individual
figures and sequential printing where the printer's clearance checks permit it.
The new print preset disables supports and the wipe tower, and enables sequential
printing. Check clearances whenever adding multiple objects.

| Setting | Previous saved value | Cool Detail v1 |
| --- | --- | --- |
| Slow down below layer time | 10 s | 20 s |
| Minimum print speed | 15 mm/s | 3 mm/s |
| External perimeter width | 0.25 mm | 0.23 mm |
| External / small perimeter speed | 18 mm/s | 12 mm/s |
| Normal retraction | 0.8 mm inherited | 0.9 mm filament override |
| Retraction speed / wipe | 35 mm/s / on inherited | 35 mm/s / on explicit override |
| Rear seam gap | 15% | 10% |

Keep fixed 0.05 mm layers and 100% fan after the initial ramp (off on layer one,
full by layer three). External-perimeter acceleration remains **220 mm/s²**,
already gentler than the proposed 400; travel acceleration remains 2500 mm/s².
Avoid crossing perimeters and the existing pressure advance remain in use.

The 20-second threshold asks the slicer to slow down; the 3 mm/s speed floor
can still leave shorter layers. It does not insert a guaranteed 20-second dwell.
See [Prusa's cooling behavior](https://help.prusa3d.com/article/cooling_127569).
Arachne can vary individual extrusion widths around the 0.23 mm nominal outer
width. Upright geometry and fixed layers remain unchanged for this comparison.
Simultaneous printing, tilt, adaptive layers and further temperature or pressure
advance tuning are separate experiments.

The [delta recipe](../specs/prusa-cool-detail-v1.json) records source names and
changes. Prepare copies without modifying installed inputs using:

```powershell
py -3.13 scripts/prepare-cool-detail-profiles.py --datadir "$env:APPDATA/PrusaSlicer" --output out/new-cool-detail-presets
```

This creates two full preset copies, an importable config bundle and source/output
hashes in a fresh output folder. Local profile dumps stay out of source control.
The original sources are `0.05mm ULTRADETAIL @XLIS 0.25 - Balanced Miniatures`
and `Epic FDM PLA`; their saved settings and vendor inheritance are retained
except for the documented overrides.

Verification on 2026-09-20 reopened the saved single-mini project and sliced it
with embedded settings only. All mesh, placement and scale entries are identical
to the prior fuller-arms test. G-code confirms the new settings, tool 2,
temperatures, fan, acceleration and existing pressure advance. Estimated time is
**1 h 16 min 50 s**, versus **24 min 52 s** previously.
Local project: `out/cool-detail-test-20260920/single-mini-cool-detail-v1.3mf`.
This verifies profile application; physical quality remains to be compared.
Existing unchecked Blender geometry and its known overhang risks are unchanged.

The screenshot shows preset selectors, not the full settings pages. Its print
label is truncated and appears modified. The support override is visible;
any other unsaved edits cannot be recovered from that image alone. This record
originally used the named saved presets plus those explicit preferences. The new
pair applies the subsequent feedback recorded above.

These selections supersede the older custom printer name
`Original Prusa XL - 5T 0.25 nozzle - Miniatures`, Generic PLA on tool 2, and
old build-local profile snapshots for **future tests**. Historical print files,
evidence and the historical proof adapter remain unchanged. Do not use the
legacy `prusa.resolve_profile()` selection for new tests without adapting it to
these presets; that adapter still targets the historical proof configuration.

On 2026-09-21 the user reported that printing multiple minis at once worked okay.
The active [five-mini wider-shield trial](wider-shield-trial.md) retains 40 mm
spacing and the 10 mm/s / 10 s cooling overrides. All five poses and the extra
glue-in base print layer by layer on tool 2; the earlier request for a separate
tool-5/base-first stage was cancelled. The final saved project was reopened and
sliced with embedded settings only: 458 layers, tool 2 only, about 3 h 2 min.
