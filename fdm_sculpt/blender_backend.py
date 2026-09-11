"""Parameterized primitives, ordered Exact CSG, rendering and mesh evidence.

This focused backend retains only the generic operations used by elf recipes.
All dimensions are millimeters. No edit-mode or sculpt-mode operations are used.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import struct
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = bmesh = Matrix = Vector = BVHTree = None

SOURCE_COLLECTION = "SOURCE_PRIMITIVES"
EXPORT_COLLECTION = "EVALUATED_EXPORT"
PALETTE = {"ivory": "#D2C5A2"}


class BlenderBackendError(RuntimeError):
    """Raised for invalid jobs or unavailable Blender functionality."""


def canonical_json(value: Any) -> str:
    """Return stable JSON used both on stdout and for generated manifests."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def safe_id(value: Any, fallback: str = "part") -> str:
    """Turn an arbitrary JSON identifier into a filesystem-safe stable id."""

    text = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "").strip())
    text = text.strip("._-")
    return text[:96] or fallback


def _hex_rgba(hex_colour: str) -> tuple[float, float, float, float]:
    value = hex_colour.lstrip("#")
    # Blender's material base colours are linear, so convert sRGB channels.
    def linear(channel: int) -> float:
        srgb = channel / 255.0
        return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4

    return (linear(int(value[0:2], 16)), linear(int(value[2:4], 16)), linear(int(value[4:6], 16)), 1.0)


class _BuildContext:
    def __init__(self, scene: Any):
        self.scene = scene
        self.source_root = bpy.data.collections.new(SOURCE_COLLECTION)
        self.export_root = bpy.data.collections.new(EXPORT_COLLECTION)
        scene.collection.children.link(self.source_root)
        scene.collection.children.link(self.export_root)
        self.source_parts: dict[str, Any] = {}
        self.export_parts: dict[str, Any] = {}
        self.atom_parts: dict[str, Any] = {}
        self.source_objects: dict[str, list[Any]] = {}
        self.export_objects: dict[str, list[Any]] = {}
        self.atom_objects: dict[str, list[Any]] = {}
        self.master_objects: dict[str, Any] = {}
        self.connectors: dict[str, list[dict[str, Any]]] = {}
        self.global_voids: dict[str, list[Any]] = {}
        self.part_origins: dict[str, Any] = {}
        self.serial = 0
        self.materials: dict[str, Any] = {}

        for semantic, hex_colour in PALETTE.items():
            material = bpy.data.materials.new(f"forge_{semantic}")
            material.diffuse_color = _hex_rgba(hex_colour)
            material["semantic"] = semantic
            material["hex"] = hex_colour
            self.materials[semantic] = material

    def begin_part(self, part: Mapping[str, Any]) -> "_PartBuilder":
        part_id = str(part["part_id"])
        src = bpy.data.collections.new(f"SRC__{part_id}")
        exp = bpy.data.collections.new(f"EXP__{part_id}")
        atoms = bpy.data.collections.new(f"EVAL_ATOMS__{part_id}")
        self.source_root.children.link(src)
        self.export_root.children.link(exp)
        exp.children.link(atoms)
        src["part_id"] = part_id
        src["kind"] = str(part["kind"])
        src["variant"] = str(part["variant"])
        exp["part_id"] = part_id
        self.source_parts[part_id] = src
        self.export_parts[part_id] = exp
        self.atom_parts[part_id] = atoms
        self.source_objects[part_id] = []
        self.export_objects[part_id] = []
        self.atom_objects[part_id] = []
        self.connectors[part_id] = []
        self.global_voids[part_id] = []
        self.part_origins[part_id] = Vector(tuple(float(value) for value in part["position"]))
        return _PartBuilder(self, part, src)

    def next_name(self, part_id: str, role: str) -> str:
        self.serial += 1
        return f"src__{safe_id(part_id)}__{safe_id(role)}__{self.serial:04d}"


def _link_only(obj: Any, collection: Any) -> None:
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _active(obj: Any) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


class _PartBuilder:
    def __init__(self, context: _BuildContext, part: Mapping[str, Any], source_collection: Any):
        self.context = context
        self.part = dict(part)
        self.part_id = str(part["part_id"])
        self.kind = str(part["kind"])
        self.variant = str(part["variant"])
        self.origin = Vector(tuple(float(v) for v in part["position"]))
        self.collection = source_collection

    def world(self, location: Sequence[float]) -> tuple[float, float, float]:
        return tuple(self.origin + Vector(tuple(float(v) for v in location)))

    @staticmethod
    def measure(obj: Any, family: str, minimum_mm: float, **values: float) -> Any:
        obj["primitive_family"] = family
        obj["measured_min_feature_mm"] = float(minimum_mm)
        for key, value in values.items():
            obj[key] = float(value)
        return obj

    def finish(
        self,
        obj: Any,
        role: str,
        semantic: str,
        *,
        export: bool = True,
        bevel: float = 0.0,
    ) -> Any:
        obj.name = self.context.next_name(self.part_id, role)
        obj.data.name = f"mesh__{obj.name}"
        _link_only(obj, self.collection)
        obj["part_id"] = self.part_id
        obj["part_kind"] = self.kind
        obj["variant"] = self.variant
        obj["role"] = role
        obj["semantic"] = semantic
        obj["export_geometry"] = bool(export)
        if semantic in self.context.materials:
            obj.data.materials.append(self.context.materials[semantic])
        if bevel > 0.0:
            modifier = obj.modifiers.new(f"bevel__{safe_id(role)}", "BEVEL")
            modifier.width = float(bevel)
            modifier.segments = 2
            modifier.limit_method = "ANGLE"
        self.context.source_objects[self.part_id].append(obj)
        return obj

    def cube(
        self,
        role: str,
        dimensions: Sequence[float],
        location: Sequence[float],
        semantic: str,
        *,
        rotation: Sequence[float] = (0.0, 0.0, 0.0),
        bevel: float = 0.2,
        export: bool = True,
    ) -> Any:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=self.world(location), rotation=rotation)
        obj = bpy.context.object
        obj.dimensions = tuple(float(v) for v in dimensions)
        _active(obj)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        result = self.finish(obj, role, semantic, export=export, bevel=bevel)
        return self.measure(result, "box", min(float(v) for v in dimensions))

    def sphere(
        self,
        role: str,
        dimensions: Sequence[float],
        location: Sequence[float],
        semantic: str,
        *,
        segments: int = 20,
        ring_count: int = 10,
        export: bool = True,
    ) -> Any:
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=int(segments),
            ring_count=int(ring_count),
            radius=1.0,
            location=self.world(location),
        )
        obj = bpy.context.object
        dims = tuple(float(v) for v in dimensions)
        obj.scale = (dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0)
        _active(obj)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        result = self.finish(obj, role, semantic, export=export)
        return self.measure(result, "ellipsoid", min(float(v) for v in dimensions))

    def cylinder(
        self,
        role: str,
        radius: float,
        depth: float,
        location: Sequence[float],
        semantic: str,
        *,
        axis: str = "Z",
        rotation: Sequence[float] | None = None,
        vertices: int = 32,
        end_fill_type: str = "NGON",
        bevel: float = 0.12,
        export: bool = True,
    ) -> Any:
        axis_rotation = {
            "X": (0.0, math.pi / 2.0, 0.0),
            "Y": (math.pi / 2.0, 0.0, 0.0),
            "Z": (0.0, 0.0, 0.0),
        }[axis.upper()]
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=vertices,
            radius=float(radius),
            depth=float(depth),
            end_fill_type=str(end_fill_type),
            location=self.world(location),
            rotation=tuple(rotation) if rotation is not None else axis_rotation,
        )
        result = self.finish(bpy.context.object, role, semantic, export=export, bevel=bevel)
        return self.measure(
            result,
            "cylinder",
            min(float(radius) * 2.0, float(depth)),
            measured_diameter_mm=float(radius) * 2.0,
            measured_depth_mm=float(depth),
        )

    def cone(
        self,
        role: str,
        radius1: float,
        radius2: float,
        depth: float,
        location: Sequence[float],
        semantic: str,
        *,
        axis: str = "Z",
        vertices: int = 8,
        export: bool = True,
    ) -> Any:
        rotation = {
            "X": (0.0, math.pi / 2.0, 0.0),
            "Y": (math.pi / 2.0, 0.0, 0.0),
            "Z": (0.0, 0.0, 0.0),
        }[axis.upper()]
        bpy.ops.mesh.primitive_cone_add(
            vertices=vertices,
            radius1=float(radius1),
            radius2=float(radius2),
            depth=float(depth),
            end_fill_type="NGON",
            location=self.world(location),
            rotation=rotation,
        )
        result = self.finish(bpy.context.object, role, semantic, export=export, bevel=0.1)
        radial_span = max(float(radius1), float(radius2)) * 2.0
        return self.measure(result, "cone", min(radial_span, float(depth)))

    def between(
        self,
        role: str,
        start: Sequence[float],
        end: Sequence[float],
        radius: float,
        semantic: str,
        *,
        bevel: float = 0.1,
        export: bool = True,
    ) -> Any:
        p1 = self.origin + Vector(tuple(float(v) for v in start))
        p2 = self.origin + Vector(tuple(float(v) for v in end))
        delta = p2 - p1
        length = delta.length
        if length <= 1e-6:
            raise BlenderBackendError(f"zero-length cylinder requested for {role}")
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=float(radius),
            depth=float(length),
            end_fill_type="NGON",
            location=tuple((p1 + p2) / 2.0),
        )
        obj = bpy.context.object
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(delta.normalized())
        result = self.finish(obj, role, semantic, export=export, bevel=bevel)
        return self.measure(
            result,
            "rod",
            float(radius) * 2.0,
            measured_diameter_mm=float(radius) * 2.0,
            measured_depth_mm=float(length),
        )

    def boolean(
        self,
        target: Any,
        cutter: Any,
        operation: str = "DIFFERENCE",
        *,
        double_threshold: float = 0.001,
    ) -> Any:
        modifier = target.modifiers.new(
            f"exact_{operation.lower()}__{safe_id(cutter.get('role', cutter.name))}", "BOOLEAN"
        )
        modifier.operation = operation
        modifier.solver = "EXACT"
        modifier.object = cutter
        modifier.double_threshold = float(double_threshold)
        cutter.hide_render = True
        return modifier

    def bevel(
        self,
        obj: Any,
        width: float,
        *,
        role: str | None = None,
        segments: int = 2,
        limit_method: str = "ANGLE",
    ) -> Any:
        """Add a deterministic bevel without exposing Blender to recipes."""

        modifier = obj.modifiers.new(
            f"bevel__{safe_id(role or obj.get('role', obj.name))}", "BEVEL"
        )
        modifier.width = float(width)
        modifier.segments = int(segments)
        modifier.limit_method = str(limit_method)
        return modifier


def _copy_properties(source: Any, target: Any) -> None:
    for key in (
        "part_id",
        "part_kind",
        "variant",
        "role",
        "semantic",
        "connector_spec",
        "construction",
        "anatomy_role",
        "primitive_family",
        "measured_min_feature_mm",
        "measured_diameter_mm",
        "measured_depth_mm",
        "measured_negative_relief_mm",
        "implicit_resolution_mm",
        "implicit_threshold",
    ):
        if key in source:
            target[key] = source[key]


def _bake_csg(
    name: str,
    base: Any,
    operands: Sequence[Any],
    operation: str,
    collection: Any,
) -> Any:
    """Evaluate an exact object-mode CSG stack into one persistent mesh."""

    work = base.copy()
    work.data = base.data.copy()
    work.name = f"work__{safe_id(name)}"
    collection.objects.link(work)
    operand_collection = None
    if len(operands) > 1:
        # Blender can evaluate a whole operand collection in one exact
        # Boolean node.  This avoids the explosive intermediate topology of a
        # long serial modifier stack while preserving the same CSG union.
        operand_collection = bpy.data.collections.new(f"csg_operands__{safe_id(name)}")
        bpy.context.scene.collection.children.link(operand_collection)
        for operand in operands:
            operand_collection.objects.link(operand)
        modifier = work.modifiers.new(f"partition_{operation.lower()}_collection", "BOOLEAN")
        modifier.operation = operation
        modifier.solver = "EXACT"
        modifier.operand_type = "COLLECTION"
        modifier.collection = operand_collection
    elif operands:
        modifier = work.modifiers.new(f"partition_{operation.lower()}_001", "BOOLEAN")
        modifier.operation = operation
        modifier.solver = "EXACT"
        modifier.object = operands[0]
    if operands:
        modifier.double_threshold = 0.001
        if hasattr(modifier, "use_self"):
            modifier.use_self = True
        if hasattr(modifier, "use_hole_tolerant"):
            modifier.use_hole_tolerant = True
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = work.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(
        evaluated,
        preserve_all_data_layers=True,
        depsgraph=depsgraph,
    )
    mesh.validate(clean_customdata=False)
    mesh.update(calc_edges=True)
    result = bpy.data.objects.new(name, mesh)
    collection.objects.link(result)
    result.matrix_world = work.matrix_world.copy()
    _copy_properties(base, result)
    old_mesh = work.data
    bpy.data.objects.remove(work, do_unlink=True)
    if operand_collection is not None:
        bpy.data.collections.remove(operand_collection)
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    return result


def _mesh_object_hash(obj: Any) -> str:
    """Hash sampled solid occupancy, independent of Boolean triangulation.

    Blender's Exact solver can choose different but geometrically equivalent
    coplanar tessellations in separate processes.  A fixed world-space
    occupancy lattice is classified independently by axis-aligned ray parity.
    A cell is retained only when at least two of three axes classify it as
    interior, making grazing-edge differences irrelevant.  Samples close to a
    boundary are omitted while 0.8 mm color features remain represented by
    multiple interior cells.
    """

    mesh = obj.data
    matrix = obj.matrix_world
    coordinates = [matrix @ vertex.co for vertex in mesh.vertices]
    bounds_min = [min(float(co[axis]) for co in coordinates) for axis in range(3)]
    bounds_max = [max(float(co[axis]) for co in coordinates) for axis in range(3)]
    polygons = [tuple(int(index) for index in polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(
        [tuple(co) for co in coordinates], polygons, all_triangles=False, epsilon=1e-7
    )
    spacing = 0.30
    offsets = (0.173, 0.417, 0.683)
    digest = hashlib.sha256()
    digest.update(b"fdm-solid-occupancy-v3")
    digest.update(struct.pack("<d", spacing))
    starts = [math.floor(bounds_min[axis] / spacing - offsets[axis]) for axis in range(3)]
    stops = [math.ceil(bounds_max[axis] / spacing - offsets[axis]) for axis in range(3)]
    digest.update(struct.pack("<6i", *(starts + stops)))
    boundary_guard = 0.04
    votes: dict[tuple[int, int, int], int] = {}
    for axis in range(3):
        perpendicular = [index for index in range(3) if index != axis]
        u_axis, v_axis = perpendicular
        direction = Vector(tuple(1.0 if index == axis else 0.0 for index in range(3)))
        ray_start = (starts[axis] - 2 + offsets[axis]) * spacing
        ray_end = (stops[axis] + 2 + offsets[axis]) * spacing
        axis_occupied: set[tuple[int, int, int]] = set()
        for u_index in range(starts[u_axis], stops[u_axis] + 1):
            u_value = (u_index + offsets[u_axis]) * spacing
            for v_index in range(starts[v_axis], stops[v_axis] + 1):
                v_value = (v_index + offsets[v_axis]) * spacing
                origin_values = [0.0, 0.0, 0.0]
                origin_values[axis] = ray_start
                origin_values[u_axis] = u_value
                origin_values[v_axis] = v_value
                origin = Vector(origin_values)
                hits: list[float] = []
                while float(origin[axis]) <= ray_end:
                    location, _normal, _face, _distance = tree.ray_cast(
                        origin, direction, ray_end - float(origin[axis])
                    )
                    if location is None:
                        break
                    depth = float(location[axis])
                    if not hits or depth - hits[-1] > 0.025:
                        hits.append(depth)
                    origin = location + direction * 0.004
                for low, high in zip(hits[0::2], hits[1::2]):
                    first = math.ceil((low + boundary_guard) / spacing - offsets[axis])
                    last = math.floor((high - boundary_guard) / spacing - offsets[axis])
                    for depth_index in range(
                        max(first, starts[axis]), min(last, stops[axis]) + 1
                    ):
                        indices = [0, 0, 0]
                        indices[axis] = depth_index
                        indices[u_axis] = u_index
                        indices[v_axis] = v_index
                        axis_occupied.add(tuple(indices))
        for indices in axis_occupied:
            votes[indices] = votes.get(indices, 0) + 1
    occupied_cells = sorted(indices for indices, count in votes.items() if count >= 2)
    for indices in occupied_cells:
        digest.update(struct.pack("<3i", *indices))
    digest.update(struct.pack("<I", len(occupied_cells)))
    return digest.hexdigest()


def _object_metrics(
    obj: Any,
    *,
    preflight_artifact: bool = True,
    include_mesh_hash: bool = True,
) -> dict[str, Any]:
    mesh = obj.data
    mesh.calc_loop_triangles()
    artifact_preflight = (
        _triangle_artifact_preflight((obj,)) if preflight_artifact else None
    )
    bm = bmesh.new()
    bm.from_mesh(mesh)
    signed_volume = float(bm.calc_volume(signed=True)) if bm.faces else 0.0
    nonmanifold_edges = [edge for edge in bm.edges if not edge.is_manifold]
    manifold = not nonmanifold_edges if bm.edges else False
    nonmanifold_samples = [
        [
            [round(float(value), 6) for value in (obj.matrix_world @ vertex.co)]
            for vertex in edge.verts
        ]
        for edge in nonmanifold_edges[:12]
    ]
    bm.free()
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bounds_min = [min(float(corner[index]) for corner in world_corners) for index in range(3)]
    bounds_max = [max(float(corner[index]) for corner in world_corners) for index in range(3)]
    result = {
        "name": obj.name,
        "role": str(obj.get("role", "geometry")),
        "semantic": str(obj.get("semantic", "charcoal")),
        "construction": str(obj.get("construction", "primitive-modifier")),
        "anatomy_role": str(obj.get("anatomy_role", "")),
        "vertices": len(mesh.vertices),
        "triangles": len(mesh.loop_triangles),
        "signed_volume_mm3": round(signed_volume, 6),
        "volume_mm3": round(abs(signed_volume), 6),
        "positive_volume": signed_volume > 1e-8,
        "manifold": bool(manifold),
        "nonmanifold_edge_count": len(nonmanifold_edges),
        "nonmanifold_edge_samples_mm": nonmanifold_samples,
        "bounds_min_mm": [round(value, 6) for value in bounds_min],
        "bounds_max_mm": [round(value, 6) for value in bounds_max],
    }
    if include_mesh_hash:
        result["mesh_hash"] = _mesh_object_hash(obj)
    if artifact_preflight is not None:
        result["artifact_preflight"] = artifact_preflight
    return result


def _self_intersection_count(obj: Any) -> int:
    """Count non-adjacent face intersections with Blender's measured BVH."""

    mesh = obj.data
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    polygons = [tuple(int(index) for index in polygon.vertices) for polygon in mesh.polygons]
    if not polygons:
        return 0
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-7)
    pairs = tree.overlap(tree)
    unique: set[tuple[int, int]] = set()
    vertex_sets = [set(polygon) for polygon in polygons]
    for left, right in pairs:
        if left >= right:
            continue
        # Adjacent triangles/polygons necessarily meet at their shared edge or
        # vertex and are not self-intersections.
        if vertex_sets[left].intersection(vertex_sets[right]):
            continue
        unique.add((int(left), int(right)))
    return len(unique)


def _triangle_artifact_preflight(objects: Sequence[Any]) -> dict[str, Any]:
    """Measure the exact part-local triangle stream written to binary STL.

    Evaluated objects carry a world-space technical-sheet translation solely
    for readable previews.  STL vertices deliberately come from object-local
    mesh data so that distant sheet positions cannot magnify float32 rounding
    into collapsed edges.  The in-memory binary round-trip is identical to the
    eventual artifact and therefore catches failures Blender's indexed-edge
    manifold flag cannot see after STL coordinate welding.
    """

    from fdm_sculpt import formats as mesh_formats
    from fdm_sculpt import validation as mesh_validation

    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    minimum_edge = math.inf
    zero_area = 0
    duplicate_coordinate_triangles = 0
    seen_coordinate_triangles: set[
        tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    ] = set()
    per_object: list[dict[str, Any]] = []
    for obj in sorted(objects, key=lambda item: item.name):
        mesh = obj.data
        mesh.calc_loop_triangles()
        object_zero_area = 0
        object_minimum_edge = math.inf
        object_duplicate = 0
        object_seen: set[
            tuple[
                tuple[float, float, float],
                tuple[float, float, float],
                tuple[float, float, float],
            ]
        ] = set()
        for loop_triangle in mesh.loop_triangles:
            coordinates = tuple(
                tuple(float(value) for value in mesh.vertices[index].co)
                for index in loop_triangle.vertices
            )
            a = Vector(coordinates[0])
            b = Vector(coordinates[1])
            c = Vector(coordinates[2])
            edge_lengths = ((b - a).length, (c - b).length, (a - c).length)
            triangle_minimum = min(float(value) for value in edge_lengths)
            minimum_edge = min(minimum_edge, triangle_minimum)
            object_minimum_edge = min(object_minimum_edge, triangle_minimum)
            if (b - a).cross(c - a).length <= 1e-12:
                zero_area += 1
                object_zero_area += 1
            coordinate_key = tuple(sorted(coordinates))
            if coordinate_key in seen_coordinate_triangles:
                duplicate_coordinate_triangles += 1
            seen_coordinate_triangles.add(coordinate_key)
            if coordinate_key in object_seen:
                object_duplicate += 1
            object_seen.add(coordinate_key)
            start = len(vertices)
            vertices.extend(coordinates)
            triangles.append((start, start + 1, start + 2))
        per_object.append(
            {
                "name": obj.name,
                "triangle_count": len(mesh.loop_triangles),
                "zero_area_loop_triangles": object_zero_area,
                "duplicate_coordinate_triangles": object_duplicate,
                "minimum_edge_mm": (
                    round(object_minimum_edge, 12)
                    if math.isfinite(object_minimum_edge)
                    else None
                ),
            }
        )

    if not triangles:
        return {
            "method": "part-local loop triangles plus exact binary-STL float32 round-trip",
            "coordinate_frame": "part-local object mesh coordinates",
            "passes": False,
            "failure": "no triangles",
            "triangle_count": 0,
            "objects": per_object,
        }

    source_mesh = mesh_formats.Mesh(tuple(vertices), tuple(triangles))
    binary = mesh_formats.dumps_binary_stl(source_mesh, name="fdm-artifact-preflight")
    reopened = mesh_formats.loads_stl(binary)
    try:
        sanitized = mesh_formats.sanitize_stl_mesh(reopened)
    except Exception as exc:
        return {
            "method": "part-local loop triangles plus exact binary-STL float32 round-trip",
            "coordinate_frame": "part-local object mesh coordinates",
            "triangle_count": len(triangles),
            "zero_area_loop_triangles": zero_area,
            "duplicate_coordinate_triangles": duplicate_coordinate_triangles,
            "minimum_edge_mm": round(minimum_edge, 12),
            "binary_size_bytes": len(binary),
            "sanitization_error": f"{type(exc).__name__}: {exc}",
            "objects": per_object,
            "passes": False,
        }
    analysis = mesh_validation.analyze_mesh(sanitized.mesh)
    sanitization = sanitized.to_dict()
    topology = {
        "triangle_count": analysis.triangle_count,
        "boundary_edges": analysis.boundary_edges,
        "nonmanifold_edges": analysis.nonmanifold_edges,
        "inconsistently_oriented_edges": analysis.inconsistently_oriented_edges,
        "degenerate_triangles": analysis.degenerate_triangles,
        "duplicate_triangles": analysis.duplicate_triangles,
        "connected_components": analysis.connected_components,
        "signed_volume_mm3": round(analysis.signed_volume_mm3, 9),
        "component_signed_volumes_mm3": [
            round(value, 9) for value in analysis.component_signed_volumes_mm3
        ],
        "watertight": analysis.watertight,
        "manifold": analysis.manifold,
        "outward_facing": analysis.outward_facing,
        "positive_volume": analysis.positive_volume,
    }
    passes = bool(
        zero_area == 0
        and duplicate_coordinate_triangles == 0
        and minimum_edge > 0.0
        and sanitized.removed_triangle_count == 0
        and analysis.watertight
        and analysis.manifold
        and analysis.outward_facing
        and analysis.positive_volume
    )
    return {
        "method": "part-local loop triangles plus exact binary-STL float32 round-trip",
        "coordinate_frame": "part-local object mesh coordinates",
        "triangle_count": len(triangles),
        "zero_area_loop_triangles": zero_area,
        "duplicate_coordinate_triangles": duplicate_coordinate_triangles,
        "minimum_edge_mm": round(minimum_edge, 12),
        "binary_size_bytes": len(binary),
        "sanitization": sanitization,
        "reopened_topology": topology,
        "objects": per_object,
        "passes": passes,
    }


def _export_stl(path: Path, objects: Sequence[Any]) -> dict[str, Any]:
    """Write one clean part-local STL and independently reopen its bytes."""

    from fdm_sculpt import formats as mesh_formats
    from fdm_sculpt import validation as mesh_validation

    selected = tuple(objects)
    preflight = _triangle_artifact_preflight(selected)
    if not preflight["passes"]:
        raise BlenderBackendError(
            f"STL preflight rejected dirty evaluated geometry for {path.name}: "
            f"{canonical_json(preflight)}"
        )

    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for obj in sorted(selected, key=lambda item: item.name):
        obj.data.calc_loop_triangles()
        for loop_triangle in obj.data.loop_triangles:
            start = len(vertices)
            vertices.extend(
                tuple(float(value) for value in obj.data.vertices[index].co)
                for index in loop_triangle.vertices
            )
            triangles.append((start, start + 1, start + 2))

    path.parent.mkdir(parents=True, exist_ok=True)
    mesh_formats.write_binary_stl(
        path,
        mesh_formats.Mesh(tuple(vertices), tuple(triangles)),
        name=path.stem,
    )
    try:
        reopened = mesh_formats.read_stl(path)
        sanitized = mesh_formats.sanitize_stl_mesh(reopened)
        analysis = mesh_validation.analyze_mesh(sanitized.mesh)
        if sanitized.removed_triangle_count:
            raise BlenderBackendError(
                f"Written STL contains removal-worthy float32 triangles: "
                f"{canonical_json(sanitized.to_dict())}"
            )
        if not (
            analysis.watertight
            and analysis.manifold
            and analysis.outward_facing
            and analysis.positive_volume
        ):
            raise BlenderBackendError(
                "Written STL failed reopened topology validation: "
                + canonical_json(
                    {
                        "boundary_edges": analysis.boundary_edges,
                        "nonmanifold_edges": analysis.nonmanifold_edges,
                        "inconsistently_oriented_edges": analysis.inconsistently_oriented_edges,
                        "degenerate_triangles": analysis.degenerate_triangles,
                        "duplicate_triangles": analysis.duplicate_triangles,
                        "component_signed_volumes_mm3": analysis.component_signed_volumes_mm3,
                    }
                )
            )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if not path.is_file() or path.stat().st_size <= 84:
        raise BlenderBackendError(f"STL export did not produce a readable artifact: {path}")
    return preflight


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ensure_camera(scene: Any) -> Any:
    camera_data = bpy.data.cameras.new("technical_ortho_camera")
    camera_data.type = "ORTHO"
    camera_data.lens = 50.0
    camera_data.clip_start = 0.1
    camera_data.clip_end = 1000.0
    camera = bpy.data.objects.new("technical_ortho_camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def _render_preview(
    scene: Any,
    camera: Any,
    objects: Sequence[Any],
    path: Path,
    *,
    focus_center: Sequence[float] | None = None,
    ortho_scale: float | None = None,
    view_direction: Sequence[float] | None = None,
) -> None:
    # Toggle every renderable generated solid, not only conventional name
    # prefixes.  Persistent-void masks intentionally retain a ``voided_*``
    # construction name, and excluding that prefix allowed a same-column part
    # to appear behind a frontal orthographic proof.
    render_geometry = [obj for obj in scene.objects if obj.type in {"MESH", "META"}]
    for obj in render_geometry:
        obj.hide_render = obj not in objects

    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    mins = Vector(tuple(min(float(corner[index]) for corner in corners) for index in range(3)))
    maxs = Vector(tuple(max(float(corner[index]) for corner in corners) for index in range(3)))
    center = (
        Vector(tuple(float(value) for value in focus_center))
        if focus_center is not None
        else (mins + maxs) / 2.0
    )
    dimensions = maxs - mins
    camera_direction = (
        Vector(tuple(float(value) for value in view_direction)).normalized()
        if view_direction is not None
        else Vector((0.9, -1.6, 0.85)).normalized()
    )
    camera.location = center + camera_direction * 100.0
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = (
        float(ortho_scale)
        if ortho_scale is not None
        else max(8.0, max(dimensions.x, dimensions.z, dimensions.y * 0.75) * 1.35)
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    if not path.is_file() or path.stat().st_size < 100:
        raise BlenderBackendError(f"Preview render did not produce a readable PNG: {path}")


def _configure_scene(scene: Any, resolution: int) -> None:
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.4
    scene.display.shading.curvature_valley_factor = 1.0
    scene.display.shading.background_type = "WORLD"
    scene.render.resolution_x = int(resolution)
    scene.render.resolution_y = int(resolution)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("technical_preview_world")
    scene.world.color = (0.035, 0.04, 0.045)
