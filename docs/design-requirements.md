# Army model design requirements

The default spearmen are [locked](locked-spearmen.md), using
[`specs/elf-modular-visual.json`](../specs/elf-modular-visual.json).
The user accepted their printed shape on 2026-09-23. Keep current heads, noses,
pointed helmets, crests, raised fierce seahorses, broad shields, bodies and arms.
Every spear must lean at least 6 degrees from vertical. That final angle change
is visual-only pending a physical trial; other army variants remain unprinted.
Prior spearman experiment recipes and viewer entries have been deleted.

## Printer and scale

- Python 3.13, Blender 5.1.2 and PrusaSlicer 2.9.6.
- Five-tool Prusa XL, tool 2, 0.25 mm nozzle, PLA, 0.05 mm layers.
- Preserve the nozzle array `0.4,0.25,0.4,0.4,0.4` and installed presets.
- Source scale is 8 mm sole-to-eye; apply the 1.3 export scale exactly once.
- Current printed spear shaft: 1.82 mm, uniform along its length.
- Separate footings: 5.2 x 6.5 x 1.3 mm. Shared base: 37.5 x 8.4 x 2 mm.
- Use the [default print recipe](../specs/prusa-spearmen.json): five minis spaced
  at least 40 mm apart and the additional base, layer by layer on tool 2.
- Resolve the [saved presets](prusa-print-test-settings.md) read-only. Keep
  205 C normal layers, 230 C first layer, supports off and 100% cooling after
  the initial ramp. Tool-2 overrides: 10 mm/s minimum speed and 10 s slowdown.

## Geometry and validation

- Generate only parameterized primitives, transforms, bevels and ordered Exact
  CSG. Never sculpt, hand-edit mesh elements or import third-party meshes.
  Terrain-specific exception requested by the user: continuous procedural
  heightfields may replace the former dirt/sand primitive textures. Generate
  these algorithmically from pinned seeded samples; no manual mesh edits or
  imported heightmaps. Figures and base bodies retain the primitive/Exact rules.
- Reusable recipes live in `fdm_sculpt/components/`, import no Blender modules,
  own their geometry and landmarks, and use explicit positive integer revisions.
  Preserve reviewed definitions and golden hashes; change geometry in a new revision.
- Persist component ID/version, instance ID, definition and plan hashes, geometry
  roles and Exact operation order. Keep hidden operands in `SOURCE_PRIMITIVES`
  and the fused printable strip in `EVALUATED_EXPORT`.
- Require an explicit integer seed and fresh output directory. Repeat the same
  seed independently and compare geometry hashes. Add resolver, golden hash and
  saved-Blender provenance checks for each component revision.
- Prototype targets: 0.75 mm structural walls, 1.0 mm spear shafts, 0.25 mm
  attached relief and 0.5 mm intentional gaps. Tapered terminal tips and edges of
  fused decorative relief are not freestanding structural walls.
- Require one connected watertight manifold outward-facing positive-volume
  solid without self-intersections. Check feature dimensions and spacing on the
  evaluated mesh, then inspect actual sliced layers and tool assignments.
- Keep saved nozzle configuration `0.4,0.25,0.4,0.4,0.4`. Resolve and hash installed
  profiles into the build; never edit installed presets. Reopen the exported
  Prusa project and slice without a separate config to verify it is complete.
- Label only passing builds `digitally validated`; never claim physical print
  testing without an actual user-run trial. Visual review alone is insufficient.
- Use zero removable supports as the design target. Run `regiment assess`
  on fresh sliced builds; use `--support-audit` for a separate conservative
  automatic-support estimate. Follow `docs/printability.md` for anchored bridge,
  deposited-layer and facial-detail criteria. Do not weaken gates to pass a model.
- Preserve the approved helmet outline and shared long planar nose character.
  Check filled brow/temple landmarks and actual sliced eye, mouth and nose detail.
  Geometry probes alone do not establish that small facial relief will print.
- The user does not model in Blender. Unsaved GUI changes may be discarded when
  replacing a review scene. Keep active saved builds and immutable part caches.
  Retired spearman experiment reviews must remain removed.
