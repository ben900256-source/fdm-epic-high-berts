# Wider shields and five-mini print trial

The user accepted this physical print on **2026-09-22**: “this is really good.
I think we've cracked it.” Source commit `01761b3` and the project below are the
accepted infantry baseline. Keep the more raised flat seahorse
(`aurelian.readable-insignia-trial@4`, 0.39 mm relief at print scale). Keep
shield faces readable from the front and avoid pronounced inward rotation.

The shield is 12% wider: 3.900 mm across at the 1.3 print scale, up from
3.482 mm. New immutable `aurelian.shield@6` preserves its height, thickness,
mount and pointed outline. The raised flat seahorse, current faces, hands,
uniform shafts and fuller decorative spearheads are unchanged.

Five distinct poses are pinned in `specs/experiments/wider-shield-infantry-*-trial.json`.
Run `py -3.13 scripts/generate-wider-shield-trial.py` to reproduce the definitions,
assembly references and golden hashes. Visual reviews reuse unchanged caches.

The new `aurelian.glue-tray-five-walled@2` base is 37.5 × 8.4 × 2 mm at print
scale. Pocket dimensions remain 5.5 × 6.8 × 1.2 mm, with 0.15 mm clearance per
side around the existing footings and a 0.8 mm floor. Recess pitch increases from
6.3 to 7.6 mm: the old spacing caused a small collision between poses 3 and 4.
The revised row has zero evaluated overlap between adjacent figures.

The [print recipe](../specs/prusa-five-wider-shield-trial.json) contains five
spaced minis and one extra base. All six pieces print layer by layer on tool 2
with its 0.25 mm nozzle. The user cancelled the initial tool-5/base-first setup.
Use the installed Epic Cool Detail v1 profiles, resolved read-only, with
0.05 mm layers, 205°C normal / 230°C first layer, supports off, and tool-2
cooling overrides of 10 mm/s minimum speed and 10 seconds slowdown threshold.
The user reports that the prior multi-mini print worked okay.

Local project: `out/wider-shield-print-20260921/five-wider-shield-minis-and-base-v2.3mf`.
Local evidence includes profile hashes, saved-scene provenance, viewer revision
checks, an adjacent-fit check, the final slice and print record. Source recipes
stay at their original scale; STL exports apply 1.3 exactly once.

The geometry is unchecked Blender Manifold output for a physical trial, not a
digitally validated manufacturing build. No independent repeat build or full
mesh printability audit was performed. User acceptance establishes a successful
physical print; detailed glue-fit measurements and manufacturing validation
were not reported.
