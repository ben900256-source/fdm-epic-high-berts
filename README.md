# Epic High Berts

The default is the [locked five-spearman design](docs/locked-spearmen.md), with
pointed helmets, raised seahorse shields, uniform decorative spears and glue-in
footings. All spears lean at least 6 degrees. The user accepted the printed
shape; the final spear-angle change still needs a print trial.

Source figures are 8 mm sole-to-eye. Apply the pinned **1.3 scale once** for
10.4 mm sole-to-eye figures with **1.82 mm shafts**, and a separate
**37.5 x 8.4 x 2 mm** five-recess base. Current definitions are pinned in
[the baseline](specs/spearmen-locked-baseline.json) and
[print target](specs/elf-print-target.json).

Earlier spearman experiments and their viewer entries have been removed.
Shared component definitions and golden hashes remain because current figures
and validation tools depend on them. Git history contains the retired work.

## Review

Use Python 3.13 and Blender 5.1.2. Compose the current parts from immutable caches:

```powershell
py -3.13 -m fdm_sculpt.atelier compose specs/elf-modular-visual.json --seed 1001 --output out/spearmen-review
npm --prefix viewer ci
py -3.13 -m fdm_sculpt.viewer serve
```

Open **http://127.0.0.1:8765**. It opens the locked spearmen automatically.
**Saved reviews** contains current units and parts. **Model review** selects
individual Spearmen, Swordsmen, Archers or Bertmasters; **Build a row** creates
custom five-model combinations. Other army models remain available and visual-only.

Publishing another unit does not change the default. Existing saved reviews can
be published without recomputing geometry:

```powershell
py -3.13 -m fdm_sculpt.viewer publish out/spearmen-review
```

Use Ctrl-hover to identify a geometry piece, isolate components, and save
sculpting feedback with its model revision and camera. Each compose uses a
fresh output directory. Blender is a background geometry tool.

## Printing

Use [the default spaced print recipe](specs/prusa-spearmen.json) with
[the saved print-test settings](docs/prusa-print-test-settings.md): PrusaSlicer
2.9.6, XL 5T, tool 2 with a 0.25 mm nozzle, 0.05 mm layers and supports off.
Five models and the extra base print layer by layer, with at least 40 mm figure
spacing and 10 mm/s / 10 s cooling overrides. Resolve installed profiles
read-only; local profile dumps and generated print files are not distributed.

The viewer's custom compact-row exporter uses its separate 20 x 5 mm source
strip and optional magnet pockets. It is not the accepted glue-in layout.
It performs a Blender Manifold union and native STL export, labeled **unchecked
Blender output**, without independent repeat builds, mesh validation or slicing.
The worker preserves model geometry; it does not automatically repair poses.

Only builds passing the full manufacturing workflow may be called
**digitally validated**. See [printability](docs/printability.md),
[design requirements](docs/design-requirements.md),
[construction rules](docs/construction.md) and [reusable parts](docs/reusable-parts.md).
Historical backend proof fixtures remain available for regression checks;
they are not the current default models.

Generated geometry, print files, feedback and immutable caches live under the
ignored `out/` directory. This repository contains procedural source and its
verification records.
