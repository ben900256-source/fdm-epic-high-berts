# Three-mini cooling comparison

The user reported worse regular rings on the spear after the slow Cool Detail v1
single-mini print. The proposed thermal/low-flow explanation is a hypothesis;
the next experiment isolates cooling behavior before changing temperature, flow,
retraction or acceleration.

[Trial settings](../specs/prusa-three-mini-cooling-trial.json):

- Three identical instances, 40 mm center-to-center along X.
- Print all three at each layer (`complete_objects=0`).
- Tool-2 minimum print speed: 10 mm/s, previously 3.
- Tool-2 slowdown threshold: 10 seconds, previously 20.
- Everything else retained: 0.25 mm nozzle, 0.05 mm layers, 205°C normal / 230°C
  first layer, 100% fan after its existing initial ramp, 0.23 mm external width,
  0.9 mm retraction with wiping, current pressure advance and extrusion multiplier,
  and 220 mm/s² external acceleration.

The source is the mesh in the last single-mini Cool Detail project, including
the previous projecting insignia. The newer raised flat shield remains available
as a separate geometry trial. Keeping this mesh unchanged makes the cooling
comparison easier to interpret. Its existing 130% scale is retained exactly once.

The installed presets and their vendor inheritance were resolved read-only and
compared to the previous project's settings before applying the three overrides.
The new 3MF embeds its complete settings and is reopened and sliced without a
separate config. Mesh resources remain unchanged; only build instances and
settings are edited. Installed presets are not modified.

Project: `out/three-mini-cooling-20260921/three-mini-cooling-10mm-10s.3mf`.
The output folder contains G-code, profile input hashes and verification results.
G-code verification confirms that all three instances extrude on every one of
the 408 layers, from Z=0.14 to 20.49 mm. Estimated normal-mode print time is
**1 h 31 min 10 s total**; extrusion multiplier is **1.00**.
Existing unchecked Blender geometry is reused; this is not a new digitally
validated manufacturing build. Physical comparison is pending.

Compare spear rings and body definition with the previous print before trying
200°C or separate extrusion-multiplier trials. The threshold is a slowdown
target constrained by minimum speed, not a guaranteed layer-time pause;
see [Prusa's cooling documentation](https://help.prusa3d.com/article/cooling_127569).
