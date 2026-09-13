# Army model design requirements

Use this as the starting point when designing a new piece or army variant.
[Repository rules](../AGENTS.md) govern construction;
[printability criteria](printability.md) define release checks;
[reusable parts](reusable-parts.md) describes the review workflow.

## Printer and scale

- Five-tool Prusa XL, tool 2, 0.25 mm nozzle, single-color PLA, 0.05 mm layers.
- Preserve the nozzle array `0.4,0.25,0.4,0.4,0.4` and installed presets.
- Python 3.13, Blender 5.1.2 and PrusaSlicer 2.9.5 are the pinned tools.
- The reference infantry are 8 mm sole-to-eye, five figures on a
  20 x 5 x 1 mm strip. New army layouts may compose other figures and bases.

## Geometry targets

| Feature | Prototype target |
| --- | --- |
| Structural stock | At least 0.75 mm |
| Spear shafts | At least 1.0 mm diameter |
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
