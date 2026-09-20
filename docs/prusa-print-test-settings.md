# Future PrusaSlicer print-test settings

The user selected these presets in a clipboard screenshot on 2026-09-19. Their
full names and saved selections were checked against the local PrusaSlicer
configuration. Use [the settings record](../specs/prusa-print-test-settings.json)
for subsequent physical print trials.

| Setting | Selection |
| --- | --- |
| PrusaSlicer | 2.9.6 |
| Print preset | 0.05mm ULTRADETAIL @XLIS 0.25 - Balanced Miniatures |
| Printer preset | Original Prusa XL - 5T Input Shaper 0.25 nozzle |
| Tool 2 filament | Epic FDM PLA |
| Other tools' filament | Generic PLA @XLIS (shown as Generic PLA in the UI) |
| Supports | None |

The saved **Epic FDM PLA** profile currently specifies **205°C printing,
230°C first layer, and 60°C bed**. Use its saved temperatures, including the
first-layer value; the preceding spear experiment's 205°C first-layer override
is superseded. Read the installed presets when preparing each new trial, so
later saved user adjustments are respected. Do not edit installed presets.

Keep tool 2 assigned to the model and preserve the physical nozzle array
`0.4,0.25,0.4,0.4,0.4`. Continue the previously requested spaced individual
figures and sequential printing where the printer's clearance checks permit it.
The saved print preset enables supports; override support generation off to
match the screenshot's **None** selection.

The screenshot shows preset selectors, not the full settings pages. Its print
label is truncated and appears modified. The support override is visible;
any other unsaved edits cannot be recovered from that image alone. This record
uses the named saved presets plus the explicit preferences above.

These selections supersede the older custom printer name
`Original Prusa XL - 5T 0.25 nozzle - Miniatures`, Generic PLA on tool 2, and
old build-local profile snapshots for **future tests**. Historical print files,
evidence and the historical proof adapter remain unchanged. Do not use the
legacy `prusa.resolve_profile()` selection for new tests without adapting it to
these presets; that adapter still targets the historical proof configuration.
