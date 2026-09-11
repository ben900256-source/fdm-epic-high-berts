# Spearman construction and validation

The latest `RegimentSpec` pins five version-10 recipes at 4 mm spacing, with sole
anchors at X = -8, -4, 0, 4 and 8 mm. Named hips, knees, ankles, hands and elbows
drive the restrained poses. The seed is explicit even though the current
recipes do not make random choices.

Each figure has continuous limb cores, overlapping forearm armor and a gloved
spear grip made from a palm, grouped finger mass, thumb, cuff and knuckle plate.
Planted skirts and flared capes reinforce the legs. Rounded cloth gathers cover
the shoulders and continue into the cape. The attached shields have broad tops
and a pointed lower half, constructed with two Exact halfspace intersections.
Connected ellipsoids form a raised seahorse emblem with snout, curved neck,
belly and curled tail. Its nominal relief is 0.36 mm above the shield face.

The helmet shell wraps the back of the head and narrows into a curved pointed
crown. A rounded face aperture forms its brow and cheek guards directly in the
shell. The aperture is 1.08 mm wide, has 0.12 mm corner rounding and reaches
8.10 mm above the soles. Three projecting brow/temple plates from revision 8
are removed; the rest of the reviewed cape, shield and body geometry is retained.

Revision 10 retains that helmet and fits a broader rounded head into its
envelope. The nominal head blank is 1.48 mm wide and 1.88 mm high. An Exact
intersection limits it to the helmet interior, leaving a shallow rim recess.
Chin and nose-root volumes are unioned before subtracting rounded eye sockets
and a mouth line. The shared four-plane nose is unioned last to preserve its
outline. Evaluated head-only ray probes check brow/temple fill and eye depth;
using the head recipe avoids false probe hits on a nearby spear.

Spear shafts measure 1.02 mm in diameter. Their terminal flats have nominal
radius 0.34 mm before the 0.85 depth scaling and polygon faceting: approximately
0.67 × 0.57 mm across. This is a deliberate finite end, not an established
minimum printable size. Sharper tips require separate layer and trial-print
evaluation.

## Deterministic build

Recipes resolve without Blender into one authoritative primitive plan. The
adapter builds that plan through the generic primitive boundary and persists
component provenance on every source object. Boolean modifiers use the Exact
solver in declared order. The assembly applies a fixed 0.00001 mm numerical Weld
after the Exact union. No mesh editing or parameter-independent repairs follow.

Mesh checks inspect the evaluated object and binary-STL float32 round trip:
one connected component, no boundary/nonmanifold or inconsistently oriented
edges, positive signed volume, no duplicate/degenerate triangles and no measured
self-intersections. Ray probes measure shafts, shields, cloaks, necks, grips,
elbow joins and shoulder attachments. Projected envelopes verify 0.5 mm gaps.
Reopening the saved Blender scene verifies primitive transforms, retained
operands, export roles, operation order and component hashes.

The geometry digest samples solid occupancy; it is not a byte hash of the mesh.
Repeat evidence also compares triangle counts, bounds, volumes and resolved
plans, with SHA-256 artifact hashes recorded separately.

## Print evidence

The profile adapter resolves printer, print and filament inheritance and records
input/snapshot hashes. It validates the selected nozzle at index 1. Perimeter,
infill, solid infill and adhesion extrusion select tool 2. PrusaSlicer first
exports geometry and normalized settings; the adapter adds these settings and
object/volume tool assignments to the project archive. A second invocation
reopens and slices that project without loading another configuration.

Validation requires successful stage-specific logs and fresh readable files.
Plain-text G-code is checked for PrusaSlicer version, machine, nozzle/layer
metadata and model extrusion on `T1`. Rasterized layer evidence compares model
cross sections and deposited paths, checks disconnected starts and limits local
lateral growth to one 0.25 mm extrusion width at 0.025 mm sampling.

These are prototype digital checks. They do not establish physical durability
or universally prove minimum wall thickness from a finite set of probes.
Latest revision status and measured results are recorded in `proof/review.json`.
The additional [printability screen](printability.md) checks deposited G-code
against the previous layer's plastic and verifies named facial landmarks.
These are mandatory validation gates; current failures remain visible.
