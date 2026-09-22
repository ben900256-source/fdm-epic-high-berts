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
- Viewer row-export exception explicitly requested by the user: use Blender's
  Manifold Boolean Union and native STL exporter, accepting Blender's result
  without geometry validation, independent repeat builds or slicing. Label these
  downloads unchecked Blender output. Keep the existing model recipes unchanged;
  the historical manufacturing gates below still apply to validated proof builds.
- Current accepted infantry baseline: [wider-shield glue-in spearmen](docs/wider-shield-trial.md),
  physically printed and accepted on 2026-09-22. Preserve the more raised flat
  seahorse (`aurelian.readable-insignia-trial@4`, 0.39 mm printed relief).
  Keep shield faces readable from the front and avoid pronounced inward rotation.
  Use the pinned five-pose print recipe in `specs/prusa-five-wider-shield-trial.json`.
- Earlier accepted scale reference: [130% intact spearmen](specs/elf-print-target.json),
  five 10.4 mm sole-to-eye figures with 1.56 mm intact spear shafts on a
  26 × 6.5 × 1.3 mm strip. The user physically printed and accepted this target.
  Keep source recipes at 8 mm sole-to-eye and apply the pinned 1.3 export scale
  exactly once, including terrain and base. The separate-spear/open-grip experiment
  is retired; preserve its historical definitions but do not resume it by default.
  See [the accepted trial](docs/intact-spears-130-trial.md) for source and evidence.
  The visual parts/assembly workflow also supports isolated
  pieces, alternative models and other army units; the five-figure restrictions
  apply to the historical spearman print-proof specification only.
- Use Python 3.13, Blender 5.1.2 and the installed PrusaSlicer 2.9.6. The target is a five-tool
  Prusa XL, tool 2 with a 0.25 mm nozzle, single-color PLA and 0.05 mm layers.
- For future physical print tests, follow [the user's preset selections](specs/prusa-print-test-settings.json)
  and [their details](docs/prusa-print-test-settings.md): the Epic Cool Detail v1
  0.05 mm print preset, Original Prusa XL - 5T Input Shaper 0.25 nozzle printer,
  Epic FDM PLA - Cool Detail v1 on tool 2 and Generic PLA @XLIS on the others,
  with supports off. The user reports worse spear rings from the single-mini v1
  test. The accepted [five-mini print](specs/prusa-five-wider-shield-trial.json)
  prints five spaced poses and the extra base layer by layer on tool 2, with
  40 mm minimum figure spacing and minimum speed / slowdown threshold of 10 mm/s / 10 s.
  Resolve the named installed presets read-only instead of reusing old test INIs
  or the historical proof adapter's preset selection. The new filament preset has
  205°C normal layers and 230°C first layer; do not force both to 205°C.
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
