# Army model design requirements

Use this as the starting point when designing a new piece or army variant.
[Repository rules](../AGENTS.md) govern construction;
[printability criteria](printability.md) define release checks;
[reusable parts](reusable-parts.md) describes the review workflow.

## Printer and scale

- Five-tool Prusa XL, tool 2, 0.25 mm nozzle, single-color PLA, 0.05 mm layers.
- Preserve the nozzle array `0.4,0.25,0.4,0.4,0.4` and installed presets.
- Python 3.13, Blender 5.1.2 and the installed PrusaSlicer 2.9.6 are the pinned tools.
- Future physical trials use [the user's selected presets](prusa-print-test-settings.md):
  Epic Cool Detail v1 0.05 mm, the XL 5T Input Shaper 0.25 nozzle preset, Epic FDM
  PLA - Cool Detail v1 on tool 2 and Generic PLA on the other tools, with supports off.
  The new profile pair awaits physical comparison. Read the
  saved presets for each trial; the new filament preset specifies 205°C normal
  layers and 230°C first layer. Earlier trial snapshots are historical evidence.
- The accepted print target is [130% intact spearmen](../specs/elf-print-target.json):
  10.4 mm sole-to-eye, 1.56 mm intact shafts, five figures on a 26 x 6.5 x 1.3 mm strip.
  Source recipes remain 8 mm sole-to-eye on a 20 x 5 x 1 mm strip; apply the
  target's 1.3 scale exactly once at export or in the slicer. The user physically
  printed this version and accepted the improvement. Open-grip/separate-spear
  experiments are retired. New army layouts may compose other figures and bases.
- Current infantry previews use a 1 mm base with 0.5 mm terrain relief.
  Optional 3 x 1 mm magnet pockets use a 2 mm base to retain roof stock.

## Geometry targets

| Feature | Prototype target |
| --- | --- |
| Structural stock | At least 0.75 mm |
| Spear shafts | Accepted intact design: 1.2 mm source, 1.56 mm at print scale |
| Attached raised detail | 0.25 mm relief |
| Intentional open gaps | At least 0.5 mm |
| Removable supports | Zero |

Keep equipment joined to the model with deliberate solid overlap. Design
undersides to grow gradually from existing material; use ramps beneath
outward projections. A conservative starting aim is no more than one layer
height of sideways growth per layer. Actual sliced paths determine whether
the resulting features have support.

Terminal tips and edges of attached relief are exceptions to the structural
stock target. For spear and banner-pole tips, prefer a short narrowing taper
with a small flat or rounded end. **About 0.3-0.4 mm across the narrowest end
is provisional design guidance, not an established printable minimum.** Keep
the supporting shaft full thickness. See [terminal tips](printability.md#terminal-tips)
for measurement and validation details.

## Reusable construction and visual review

- Use parameterized primitives, transforms, bevels and ordered Exact CSG.
  Do not sculpt, hand-edit meshes or import third-party meshes.
- Each reusable piece owns its geometry and mount landmarks. Preserve existing
  definitions and golden hashes; geometry changes get a new integer revision.
- Models and units pin component references and hashes. Compile a changed
  component once; reuse its cached geometry across placements and variants.
- Review in the local Three.js viewer. Use explicit seeds, fresh output
  directories and saved-scene provenance. Keep earlier saved reviews.
- During visual iteration, defer full-model fusion, independent repeat builds,
  mesh printability audits and slicing until print/release preparation is requested.

## Before calling a model print ready

Apply the complete [printability criteria](printability.md) to the intended
modular composition. Verify a connected watertight solid, dimensions and
spacing, actual deposited detail, support behavior, and tool assignments in
the saved slicer project. Do not weaken checks to pass a model.

Visual review is not print validation. Only passing manufacturing builds may
be labeled **digitally validated**; strength, cooling and handling still need
a user-run physical trial. The current army reviews remain **visual-only**.
