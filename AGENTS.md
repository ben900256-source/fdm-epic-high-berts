# Elf proof repository rules

- Scope: five original 8 mm sole-to-eye high-elf spearmen on a 20 × 5 × 1 mm strip.
- Use Python 3.13, Blender 5.1.2 and PrusaSlicer 2.9.5. The target is a five-tool
  Prusa XL, tool 2 with a 0.25 mm nozzle, single-color PLA and 0.05 mm layers.
- Generate only parameterized primitives, transforms, bevels and ordered Exact
  CSG. Never sculpt, hand-edit mesh elements or import third-party meshes.
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
  replacing a review scene. Keep earlier saved builds.
- This source repository is explicitly authorized for public publication under
  `ben900256-source/fdm-epic-high-berts`. Keep unrelated projects, local profile
  dumps, credentials and generated scratch artifacts out of commits.
