# Default PrusaSlicer print settings

Use [the locked spearmen](locked-spearmen.md) and
[the default print recipe](../specs/prusa-spearmen.json). Five distinct poses
and the extra glue-in base print layer by layer on tool 2, with at least 40 mm
figure-center spacing. Prior comparison trials have been retired.

| Selection | Preset |
| --- | --- |
| PrusaSlicer | 2.9.6 |
| Print | 0.05mm ULTRADETAIL @XLIS 0.25 - Epic Cool Detail v1 |
| Printer | Original Prusa XL - 5T Input Shaper 0.25 nozzle |
| Tool 2 filament | Epic FDM PLA - Cool Detail v1 |
| Other tools | Generic PLA @XLIS |
| Supports | None |

Resolve the named installed presets and their inheritance read-only for each
new test, recording their input hashes. Do not substitute old build-local INIs
or the historical proof adapter's preset selection. Preserve the physical nozzle
array `0.4,0.25,0.4,0.4,0.4`; use tool 2 for all objects.

The saved PLA preset uses **205 C normal layers, 230 C first layer and 60 C bed**.
Do not force the first layer to 205 C. Keep 0.05 mm layers, 0.14 mm first layer,
100% fan after the initial ramp, 0.23 mm nominal external width, 12 mm/s external
and small perimeter speeds, 220 mm/s2 external acceleration and 2500 mm/s2 travel
acceleration. Retraction is 0.9 mm with wipe and 35 mm/s retract speed.

The installed filament preset's 20 s / 3 mm/s defaults produced worse spear
rings in a single-mini test. Always apply the accepted project overrides on tool
2: **10 s slowdown threshold and 10 mm/s minimum speed**, plus
`complete_objects = 0`, supports off and wipe tower off. These overrides do not
modify the installed presets. A slowdown threshold is not a guaranteed dwell.

The [selection record](../specs/prusa-print-test-settings.json) and
[profile recipe](../specs/prusa-cool-detail-v1.json) retain the user's saved
preferences. The latest spear-angle adjustment remains unprinted.
