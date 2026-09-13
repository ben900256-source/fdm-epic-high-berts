# Elf proof repository rules

- Use [the design requirements](docs/design-requirements.md) when designing
  new parts and army variants. Terminal-tip dimensions in
  [the tip guidance](docs/printability.md#terminal-tips) are provisional targets;
  they do not replace actual sliced-detail and physical-trial checks.
- Use the local Three.js viewer at http://127.0.0.1:8765 for visual review.
  Successful atelier compositions publish automatically; publish an existing
  saved review with `py -3.13 -m fdm_sculpt.viewer publish <output-directory>`.
  Keep its server running and verify the loaded revision. Blender is a background
  geometry tool; only open its GUI when explicitly requested, reusing any existing window.
- Current phase is visual iteration across the army. Design reusable pieces
  independently in `fdm_sculpt/components/parts/`, pin positive integer revisions,
  and compose them through `specs/elf-modular-visual.json`. Use `atelier part`
  for isolated edits and `atelier compose` for assembled review. Compile only
  changed or missing parts; reuse immutable caches and place collection instances
  for everything else. Repositioning parts must not regenerate their geometry.
  Keep renders opt-in. Do not run whole-elf recipe generation for routine edits.
  Use local Exact CSG, overlapping visual parts, saved provenance and optional
  review images. Defer manufacturing builds until explicit publication/release
  preparation or a request for print files. Skip full-strip fusion, independent
  geometry repeats, mesh printability checks and slicing in this mode. Label
  it visual-only; keep `EVALUATED_EXPORT` empty and use `VISUAL_PREVIEW`.
  The manufacturing requirements below still apply to `regiment build` and
  print-readiness work when the user resumes that phase.
- Current reference model: five original 8 mm sole-to-eye high-elf spearmen on a
  20 × 5 × 1 mm strip. The visual parts/assembly workflow also supports isolated
  pieces, alternative models and other army units; the five-figure restrictions
  apply to the historical spearman print-proof specification only.
- Use Python 3.13, Blender 5.1.2 and PrusaSlicer 2.9.5. The target is a five-tool
  Prusa XL, tool 2 with a 0.25 mm nozzle, single-color PLA and 0.05 mm layers.
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
  replacing a review scene. Keep earlier saved builds.
- This source repository is explicitly authorized for public publication under
  `ben900256-source/fdm-epic-high-berts`. Keep unrelated projects, local profile
  dumps, credentials and generated scratch artifacts out of commits.
