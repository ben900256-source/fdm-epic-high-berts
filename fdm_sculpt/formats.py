"""Deterministic mesh interchange helpers used by the FDM build pipeline.

The module deliberately has no Blender or lib3mf dependency.  Blender-side code
can hand it vertices and triangle indices, while release tooling can inspect the
resulting STL and 3MF packages in an ordinary Python process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
import re
import struct
from typing import Any, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET
from zipfile import ZIP_STORED, BadZipFile, ZipFile, ZipInfo


CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
MODEL_RELATIONSHIP = (
    "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
)
MANIFEST_RELATIONSHIP = "https://fdm-sculpt.local/relationships/manifest"
MODEL_PART = "3D/3dmodel.model"
MANIFEST_PART = "Metadata/manifest.json"
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_IDENTITY_TRANSFORM = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)

Vec3 = tuple[float, float, float]
Triangle = tuple[int, int, int]
Transform = tuple[float, ...]


class FormatError(ValueError):
    """Raised when an interchange document is invalid or unsupported."""


def _finite_float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise FormatError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FormatError(f"{label} must be a finite number") from exc
    if not math.isfinite(result):
        raise FormatError(f"{label} must be a finite number")
    return result


def _normalise_vec3(value: Sequence[float], label: str) -> Vec3:
    if len(value) != 3:
        raise FormatError(f"{label} must contain exactly three values")
    return tuple(_finite_float(component, label) for component in value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class Mesh:
    """A small, immutable indexed triangle mesh in millimetres."""

    vertices: tuple[Vec3, ...] | Sequence[Sequence[float]]
    triangles: tuple[Triangle, ...] | Sequence[Sequence[int]]

    def __post_init__(self) -> None:
        vertices = tuple(
            _normalise_vec3(vertex, f"vertex {index}")
            for index, vertex in enumerate(self.vertices)
        )
        triangles: list[Triangle] = []
        for index, triangle in enumerate(self.triangles):
            if len(triangle) != 3:
                raise FormatError(f"triangle {index} must contain exactly three indices")
            converted: list[int] = []
            for raw in triangle:
                if isinstance(raw, bool) or not isinstance(raw, int):
                    raise FormatError(f"triangle {index} contains a non-integer index")
                converted.append(raw)
            if min(converted, default=0) < 0 or max(converted, default=-1) >= len(vertices):
                raise FormatError(f"triangle {index} references a missing vertex")
            if len(set(converted)) != 3:
                raise FormatError(f"triangle {index} is degenerate")
            triangles.append(tuple(converted))  # type: ignore[arg-type]
        object.__setattr__(self, "vertices", vertices)
        object.__setattr__(self, "triangles", tuple(triangles))

    @property
    def faces(self) -> tuple[Triangle, ...]:
        """Alias used by a few Blender mesh adapters."""

        return self.triangles  # type: ignore[return-value]

    @property
    def triangle_count(self) -> int:
        return len(self.triangles)

    @property
    def bounds(self) -> tuple[Vec3, Vec3] | None:
        if not self.vertices:
            return None
        return (
            tuple(min(vertex[axis] for vertex in self.vertices) for axis in range(3)),
            tuple(max(vertex[axis] for vertex in self.vertices) for axis in range(3)),
        )  # type: ignore[return-value]


def coerce_mesh(value: Mesh | Any) -> Mesh:
    """Convert an object exposing ``vertices`` and ``triangles``/``faces``."""

    if isinstance(value, Mesh):
        return value
    if isinstance(value, Mapping):
        vertices = value.get("vertices")
        triangles = value.get("triangles", value.get("faces"))
    else:
        vertices = getattr(value, "vertices", None)
        triangles = getattr(value, "triangles", getattr(value, "faces", None))
    if vertices is None or triangles is None:
        raise FormatError("mesh must expose vertices and triangles (or faces)")
    return Mesh(vertices, triangles)


_HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")


def normalise_color(value: str) -> str:
    """Return a 3MF display colour in deterministic ``#RRGGBBAA`` form."""

    match = _HEX_COLOR.fullmatch(str(value).strip())
    if not match:
        raise FormatError(f"invalid RGB/RGBA colour: {value!r}")
    return f"#{match.group(1).upper()}{(match.group(2) or 'FF').upper()}"


@dataclass(frozen=True, slots=True)
class Material:
    name: str
    color: str
    filament_id: str | None = None

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise FormatError("material name may not be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "color", normalise_color(self.color))
        if self.filament_id is not None:
            filament_id = str(self.filament_id).strip()
            if not filament_id:
                raise FormatError("filament_id may not be blank")
            object.__setattr__(self, "filament_id", filament_id)

    @property
    def rgb(self) -> str:
        return self.color[:7]


@dataclass(frozen=True, slots=True)
class ColorVolume:
    """One aligned physical colour region represented by a 3MF mesh object."""

    name: str
    mesh: Mesh | Any
    material: Material
    transform: Transform = _IDENTITY_TRANSFORM

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise FormatError("volume name may not be empty")
        transform = tuple(_finite_float(v, "transform") for v in self.transform)
        if len(transform) != 12:
            raise FormatError("3MF transforms contain exactly 12 values")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "mesh", coerce_mesh(self.mesh))
        object.__setattr__(self, "transform", transform)


@dataclass(frozen=True, slots=True)
class ThreeMFDocument:
    volumes: tuple[ColorVolume, ...]
    manifest: Mapping[str, Any] = field(default_factory=dict)
    unit: str = "millimeter"

    @property
    def materials(self) -> tuple[Material, ...]:
        seen: set[Material] = set()
        result: list[Material] = []
        for volume in self.volumes:
            if volume.material not in seen:
                seen.add(volume.material)
                result.append(volume.material)
        return tuple(result)


def _format_float(value: float) -> str:
    value = 0.0 if value == 0.0 else value
    return format(value, ".17g")


def _triangle_normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    normal = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    magnitude = math.sqrt(sum(component * component for component in normal))
    if magnitude == 0:
        return (0.0, 0.0, 0.0)
    return tuple(component / magnitude for component in normal)  # type: ignore[return-value]


def dumps_ascii_stl(mesh: Mesh | Any, *, name: str = "fdm-sculpt") -> bytes:
    mesh = coerce_mesh(mesh)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip()) or "fdm-sculpt"
    lines = [f"solid {safe_name}"]
    for triangle in mesh.triangles:
        a, b, c = (mesh.vertices[index] for index in triangle)
        normal = _triangle_normal(a, b, c)
        lines.append("  facet normal " + " ".join(_format_float(v) for v in normal))
        lines.append("    outer loop")
        for vertex in (a, b, c):
            lines.append("      vertex " + " ".join(_format_float(v) for v in vertex))
        lines.extend(("    endloop", "  endfacet"))
    lines.append(f"endsolid {safe_name}")
    return ("\n".join(lines) + "\n").encode("ascii")


def dumps_binary_stl(mesh: Mesh | Any, *, name: str = "fdm-sculpt") -> bytes:
    mesh = coerce_mesh(mesh)
    if mesh.triangle_count > 0xFFFFFFFF:
        raise FormatError("binary STL supports at most 2^32-1 triangles")
    label = name.encode("ascii", "replace")[:80].ljust(80, b"\0")
    output = bytearray(label)
    output.extend(struct.pack("<I", mesh.triangle_count))
    for triangle in mesh.triangles:
        vertices = tuple(mesh.vertices[index] for index in triangle)
        normal = _triangle_normal(*vertices)
        values = normal + vertices[0] + vertices[1] + vertices[2]
        output.extend(struct.pack("<12fH", *values, 0))
    return bytes(output)


def write_stl(
    path: str | Path,
    mesh: Mesh | Any,
    *,
    binary: bool = True,
    name: str | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    label = name or path.stem
    data = dumps_binary_stl(mesh, name=label) if binary else dumps_ascii_stl(mesh, name=label)
    path.write_bytes(data)
    return path


def write_binary_stl(path: str | Path, mesh: Mesh | Any, *, name: str | None = None) -> Path:
    return write_stl(path, mesh, binary=True, name=name)


def write_ascii_stl(path: str | Path, mesh: Mesh | Any, *, name: str | None = None) -> Path:
    return write_stl(path, mesh, binary=False, name=name)


def _load_binary_stl(data: bytes) -> Mesh:
    if len(data) < 84:
        raise FormatError("truncated binary STL")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + triangle_count * 50
    if len(data) != expected:
        raise FormatError(f"binary STL length is {len(data)}, expected {expected}")
    vertices: list[Vec3] = []
    triangles: list[Triangle] = []
    offset = 84
    for _ in range(triangle_count):
        unpacked = struct.unpack_from("<12fH", data, offset)
        start = len(vertices)
        vertices.extend(
            tuple(float(v) for v in unpacked[index : index + 3])  # type: ignore[arg-type]
            for index in (3, 6, 9)
        )
        triangles.append((start, start + 1, start + 2))
        offset += 50
    return Mesh(vertices, triangles)


_ASCII_VERTEX = re.compile(
    rb"\bvertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",
    re.IGNORECASE,
)


def _load_ascii_stl(data: bytes) -> Mesh:
    matches = _ASCII_VERTEX.findall(data)
    if not matches or len(matches) % 3:
        raise FormatError("ASCII STL contains an invalid number of vertices")
    vertices: list[Vec3] = []
    for match in matches:
        try:
            vertices.append(tuple(float(component) for component in match))  # type: ignore[arg-type]
        except ValueError as exc:
            raise FormatError("ASCII STL contains an invalid coordinate") from exc
    return Mesh(vertices, [tuple(range(i, i + 3)) for i in range(0, len(vertices), 3)])


def loads_stl(data: bytes) -> Mesh:
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            return _load_binary_stl(data)
    return _load_ascii_stl(data)


def read_stl(path: str | Path) -> Mesh:
    return loads_stl(Path(path).read_bytes())


@dataclass(frozen=True, slots=True)
class StlSanitizationResult:
    """Deterministic, auditable cleanup of zero-area STL serialization faces."""

    mesh: Mesh
    source_triangle_count: int
    exact_welded_vertex_count: int
    removed_collapsed_triangles: int
    removed_zero_area_triangles: int
    source_signed_volume_mm3: float
    sanitized_signed_volume_mm3: float

    @property
    def removed_triangle_count(self) -> int:
        return self.removed_collapsed_triangles + self.removed_zero_area_triangles

    @property
    def signed_volume_delta_mm3(self) -> float:
        return self.sanitized_signed_volume_mm3 - self.source_signed_volume_mm3

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": "exact-float32-coordinate weld and provably zero-area face removal",
            "source_triangle_count": self.source_triangle_count,
            "sanitized_triangle_count": self.mesh.triangle_count,
            "exact_welded_vertex_count": self.exact_welded_vertex_count,
            "removed_collapsed_triangles": self.removed_collapsed_triangles,
            "removed_zero_area_triangles": self.removed_zero_area_triangles,
            "removed_triangle_count": self.removed_triangle_count,
            "source_signed_volume_mm3": self.source_signed_volume_mm3,
            "sanitized_signed_volume_mm3": self.sanitized_signed_volume_mm3,
            "signed_volume_delta_mm3": self.signed_volume_delta_mm3,
        }


def _triangle_signed_volume(a: Vec3, b: Vec3, c: Vec3) -> float:
    cross = (
        b[1] * c[2] - b[2] * c[1],
        b[2] * c[0] - b[0] * c[2],
        b[0] * c[1] - b[1] * c[0],
    )
    return (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6.0


def sanitize_stl_mesh(
    mesh: Mesh | Any,
    *,
    area_epsilon_mm2: float = 5e-13,
    max_absolute_volume_delta_mm3: float = 1e-9,
    max_relative_volume_delta: float = 1e-12,
) -> StlSanitizationResult:
    """Restore STL adjacency without concealing nonzero geometric corruption.

    Binary STL repeats three float32 coordinates for every face.  Exact-equal
    coordinates are welded; decimal rounding is intentionally not used.  Faces
    that collapse after this exact weld, or whose area is below the same
    numerical zero used by mesh validation, carry no printable surface and are
    removed.  Duplicate nonzero faces, cracks, and nonmanifold edges remain for
    the topology validator to reject.
    """

    source = coerce_mesh(mesh)
    area_epsilon = _finite_float(area_epsilon_mm2, "STL area epsilon")
    absolute_tolerance = _finite_float(
        max_absolute_volume_delta_mm3, "STL absolute volume tolerance"
    )
    relative_tolerance = _finite_float(
        max_relative_volume_delta, "STL relative volume tolerance"
    )
    if area_epsilon < 0.0 or absolute_tolerance < 0.0 or relative_tolerance < 0.0:
        raise FormatError("STL sanitization tolerances must be non-negative")

    welded_vertices: list[Vec3] = []
    lookup: dict[Vec3, int] = {}
    retained: list[Triangle] = []
    collapsed = 0
    zero_area = 0
    source_volume = 0.0
    sanitized_volume = 0.0
    double_area_limit_squared = (2.0 * area_epsilon) ** 2
    for triangle in source.triangles:
        raw_vertices = tuple(source.vertices[index] for index in triangle)
        source_volume += _triangle_signed_volume(*raw_vertices)
        converted: list[int] = []
        for raw in raw_vertices:
            if raw not in lookup:
                lookup[raw] = len(welded_vertices)
                welded_vertices.append(raw)
            converted.append(lookup[raw])
        if len(set(converted)) != 3:
            collapsed += 1
            continue
        a, b, c = (welded_vertices[index] for index in converted)
        ab = tuple(b[axis] - a[axis] for axis in range(3))
        ac = tuple(c[axis] - a[axis] for axis in range(3))
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        if sum(component * component for component in cross) <= double_area_limit_squared:
            zero_area += 1
            continue
        converted_triangle = tuple(converted)  # type: ignore[assignment]
        retained.append(converted_triangle)
        sanitized_volume += _triangle_signed_volume(a, b, c)

    volume_tolerance = max(
        absolute_tolerance,
        abs(source_volume) * relative_tolerance,
    )
    if abs(sanitized_volume - source_volume) > volume_tolerance:
        raise FormatError(
            "zero-area STL cleanup would change signed volume by "
            f"{sanitized_volume - source_volume:.12g} mm^3"
        )

    compact_vertices: list[Vec3] = []
    compact_lookup: dict[int, int] = {}
    compact_triangles: list[Triangle] = []
    for triangle in retained:
        compact: list[int] = []
        for old_index in triangle:
            if old_index not in compact_lookup:
                compact_lookup[old_index] = len(compact_vertices)
                compact_vertices.append(welded_vertices[old_index])
            compact.append(compact_lookup[old_index])
        compact_triangles.append(tuple(compact))  # type: ignore[arg-type]

    return StlSanitizationResult(
        mesh=Mesh(tuple(compact_vertices), tuple(compact_triangles)),
        source_triangle_count=source.triangle_count,
        exact_welded_vertex_count=len(welded_vertices),
        removed_collapsed_triangles=collapsed,
        removed_zero_area_triangles=zero_area,
        source_signed_volume_mm3=source_volume,
        sanitized_signed_volume_mm3=sanitized_volume,
    )


def mesh_hash(mesh: Mesh | Any) -> str:
    """Hash canonical indexed geometry without STL vertex duplication."""

    mesh = coerce_mesh(mesh)
    digest = sha256()
    digest.update(struct.pack("<QQ", len(mesh.vertices), len(mesh.triangles)))
    for vertex in mesh.vertices:
        digest.update(struct.pack("<3d", *vertex))
    for triangle in mesh.triangles:
        digest.update(struct.pack("<3Q", *triangle))
    return digest.hexdigest()


def _xml_bytes(element: ET.Element) -> bytes:
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        element, encoding="utf-8", short_empty_elements=True
    )


def _content_types_xml() -> bytes:
    ET.register_namespace("", CONTENT_TYPES_NS)
    root = ET.Element(f"{{{CONTENT_TYPES_NS}}}Types")
    ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
    ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", Extension="model", ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml")
    ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", Extension="json", ContentType="application/json")
    return _xml_bytes(root)


def _root_relationships_xml() -> bytes:
    ET.register_namespace("", REL_NS)
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    ET.SubElement(root, f"{{{REL_NS}}}Relationship", Id="rel0", Type=MODEL_RELATIONSHIP, Target=f"/{MODEL_PART}")
    return _xml_bytes(root)


def _model_relationships_xml() -> bytes:
    ET.register_namespace("", REL_NS)
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    ET.SubElement(root, f"{{{REL_NS}}}Relationship", Id="manifest", Type=MANIFEST_RELATIONSHIP, Target=f"../{MANIFEST_PART}")
    return _xml_bytes(root)


def _unique_materials(volumes: Sequence[ColorVolume]) -> tuple[Material, ...]:
    by_name: dict[str, Material] = {}
    result: list[Material] = []
    for volume in volumes:
        existing = by_name.get(volume.material.name)
        if existing is not None and existing != volume.material:
            raise FormatError(f"material name {volume.material.name!r} has conflicting definitions")
        if existing is None:
            by_name[volume.material.name] = volume.material
            result.append(volume.material)
    return tuple(result)


def _manifest_for(
    volumes: Sequence[ColorVolume],
    materials: Sequence[Material],
    supplied: Mapping[str, Any] | None,
) -> dict[str, Any]:
    manifest = dict(supplied or {})
    manifest.setdefault("schema", "fdm-sculpt-manifest-1")
    manifest.setdefault("unit", "millimeter")
    manifest.setdefault("object_count", len(volumes))
    manifest.setdefault(
        "materials",
        [
            {
                "name": material.name,
                "color": material.color,
                **({"filament_id": material.filament_id} if material.filament_id else {}),
            }
            for material in materials
        ],
    )
    manifest.setdefault(
        "objects",
        [
            {
                "name": volume.name,
                "material": volume.material.name,
                "triangles": volume.mesh.triangle_count,
                "mesh_sha256": mesh_hash(volume.mesh),
            }
            for volume in volumes
        ],
    )
    try:
        json.dumps(manifest, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise FormatError("manifest must be finite JSON data") from exc
    return manifest


def _model_xml(
    volumes: Sequence[ColorVolume],
    materials: Sequence[Material],
    manifest_json: str,
    title: str | None,
) -> bytes:
    ET.register_namespace("", CORE_NS)
    ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
    root = ET.Element(
        f"{{{CORE_NS}}}model",
        {"unit": "millimeter", "{http://www.w3.org/XML/1998/namespace}lang": "en-US"},
    )
    if title:
        metadata = ET.SubElement(root, f"{{{CORE_NS}}}metadata", name="Title")
        metadata.text = title
    # Unqualified extension names are valid XML QNames and avoid relying on a
    # package-specific namespace declaration merely to carry opaque metadata.
    metadata = ET.SubElement(root, f"{{{CORE_NS}}}metadata", name="fdm-sculpt-manifest")
    metadata.text = manifest_json
    resources = ET.SubElement(root, f"{{{CORE_NS}}}resources")
    base_materials = ET.SubElement(resources, f"{{{CORE_NS}}}basematerials", id="1")
    material_indices: dict[Material, int] = {}
    for index, material in enumerate(materials):
        material_indices[material] = index
        attributes = {"name": material.name, "displaycolor": material.color}
        ET.SubElement(base_materials, f"{{{CORE_NS}}}base", attributes)

    for object_id, volume in enumerate(volumes, 2):
        object_element = ET.SubElement(
            resources,
            f"{{{CORE_NS}}}object",
            id=str(object_id),
            type="model",
            name=volume.name,
            pid="1",
            pindex=str(material_indices[volume.material]),
        )
        if volume.material.filament_id:
            item = ET.SubElement(object_element, f"{{{CORE_NS}}}metadata", name="fdm-sculpt-filament-id")
            item.text = volume.material.filament_id
        mesh_element = ET.SubElement(object_element, f"{{{CORE_NS}}}mesh")
        vertices_element = ET.SubElement(mesh_element, f"{{{CORE_NS}}}vertices")
        for x, y, z in volume.mesh.vertices:
            ET.SubElement(
                vertices_element,
                f"{{{CORE_NS}}}vertex",
                x=_format_float(x),
                y=_format_float(y),
                z=_format_float(z),
            )
        triangles_element = ET.SubElement(mesh_element, f"{{{CORE_NS}}}triangles")
        for v1, v2, v3 in volume.mesh.triangles:
            ET.SubElement(
                triangles_element,
                f"{{{CORE_NS}}}triangle",
                v1=str(v1),
                v2=str(v2),
                v3=str(v3),
            )
    build = ET.SubElement(root, f"{{{CORE_NS}}}build")
    for object_id, volume in enumerate(volumes, 2):
        attributes = {"objectid": str(object_id)}
        if volume.transform != _IDENTITY_TRANSFORM:
            attributes["transform"] = " ".join(_format_float(value) for value in volume.transform)
        ET.SubElement(build, f"{{{CORE_NS}}}item", attributes)
    return _xml_bytes(root)


def _zip_entry(name: str, data: bytes) -> tuple[ZipInfo, bytes]:
    info = ZipInfo(name, _ZIP_TIMESTAMP)
    # Stored entries make the complete package stable even across zlib builds.
    # 3MF/OPC readers are required to support uncompressed ZIP members.
    info.compress_type = ZIP_STORED
    info.create_system = 0
    info.external_attr = 0
    return info, data


def dumps_3mf(
    volumes: Iterable[ColorVolume],
    *,
    manifest: Mapping[str, Any] | None = None,
    title: str | None = None,
) -> bytes:
    """Create a deterministic, standards-based 3MF OPC package."""

    normalised = tuple(
        volume if isinstance(volume, ColorVolume) else ColorVolume(**volume)  # type: ignore[arg-type]
        for volume in volumes
    )
    if not normalised:
        raise FormatError("a 3MF package must contain at least one volume")
    if len({volume.name for volume in normalised}) != len(normalised):
        raise FormatError("3MF volume names must be unique")
    materials = _unique_materials(normalised)
    effective_manifest = _manifest_for(normalised, materials, manifest)
    manifest_json = json.dumps(
        effective_manifest,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    entries = (
        ("[Content_Types].xml", _content_types_xml()),
        ("_rels/.rels", _root_relationships_xml()),
        (MODEL_PART, _model_xml(normalised, materials, manifest_json, title)),
        ("3D/_rels/3dmodel.model.rels", _model_relationships_xml()),
        (MANIFEST_PART, manifest_json.encode("utf-8")),
    )
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for name, data in entries:
            info, payload = _zip_entry(name, data)
            archive.writestr(info, payload)
    return output.getvalue()


def write_3mf(
    path: str | Path,
    volumes: Iterable[ColorVolume],
    *,
    manifest: Mapping[str, Any] | None = None,
    title: str | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dumps_3mf(volumes, manifest=manifest, title=title))
    return path


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    return next((item for item in element if _local_name(item) == name), None)


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [item for item in element if _local_name(item) == name]


def _parse_transform(raw: str | None) -> Transform:
    if raw is None:
        return _IDENTITY_TRANSFORM
    values = tuple(_finite_float(value, "3MF transform") for value in raw.split())
    if len(values) != 12:
        raise FormatError("3MF build transform must contain 12 values")
    return values


def _read_archive(archive: ZipFile) -> ThreeMFDocument:
    names = set(archive.namelist())
    if MODEL_PART not in names:
        raise FormatError(f"3MF is missing {MODEL_PART}")
    try:
        root = ET.fromstring(archive.read(MODEL_PART))
    except ET.ParseError as exc:
        raise FormatError("3MF model XML is invalid") from exc
    if _local_name(root) != "model":
        raise FormatError("3MF model part has the wrong root element")
    unit = root.get("unit", "millimeter")
    resources = _child(root, "resources")
    build = _child(root, "build")
    if resources is None or build is None:
        raise FormatError("3MF model must contain resources and build")

    material_lookup: dict[tuple[str, int], Material] = {}
    for group in _children(resources, "basematerials"):
        resource_id = group.get("id")
        if resource_id is None:
            raise FormatError("3MF basematerials resource is missing an id")
        for index, base in enumerate(_children(group, "base")):
            material_lookup[(resource_id, index)] = Material(
                base.get("name", f"material-{resource_id}-{index}"),
                base.get("displaycolor", "#FFFFFFFF"),
            )

    object_lookup = {
        item.get("id", ""): item for item in _children(resources, "object") if item.get("id")
    }
    volumes: list[ColorVolume] = []
    used_names: dict[str, int] = {}
    for build_item in _children(build, "item"):
        object_id = build_item.get("objectid", "")
        object_element = object_lookup.get(object_id)
        if object_element is None:
            raise FormatError(f"3MF build references missing object {object_id!r}")
        mesh_element = _child(object_element, "mesh")
        if mesh_element is None:
            raise FormatError("component-only 3MF objects are not supported by this reader")
        vertices_element = _child(mesh_element, "vertices")
        triangles_element = _child(mesh_element, "triangles")
        if vertices_element is None or triangles_element is None:
            raise FormatError(f"3MF object {object_id} has an incomplete mesh")
        vertices = [
            (
                _finite_float(vertex.get("x"), "3MF x"),
                _finite_float(vertex.get("y"), "3MF y"),
                _finite_float(vertex.get("z"), "3MF z"),
            )
            for vertex in _children(vertices_element, "vertex")
        ]
        triangles: list[Triangle] = []
        material_refs: set[tuple[str, int]] = set()
        object_pid = object_element.get("pid")
        object_pindex = object_element.get("pindex")
        if object_pid is not None and object_pindex is not None:
            material_refs.add((object_pid, int(object_pindex)))
        for triangle in _children(triangles_element, "triangle"):
            triangles.append(
                tuple(int(triangle.get(key, "-1")) for key in ("v1", "v2", "v3"))  # type: ignore[arg-type]
            )
            pid = triangle.get("pid", object_pid)
            pindex = triangle.get("p1", object_pindex)
            if pid is not None and pindex is not None:
                material_refs.add((pid, int(pindex)))
        if len(material_refs) != 1:
            raise FormatError(
                f"3MF object {object_id} must resolve to exactly one material for a colour volume"
            )
        reference = next(iter(material_refs))
        try:
            material = material_lookup[reference]
        except KeyError as exc:
            raise FormatError(f"3MF object {object_id} references a missing material") from exc
        filament_id = None
        object_metadata = list(_children(object_element, "metadata"))
        metadata_group = _child(object_element, "metadatagroup")
        if metadata_group is not None:
            object_metadata.extend(_children(metadata_group, "metadata"))
        for metadata in object_metadata:
            metadata_name = metadata.get("name", "")
            if metadata_name in {"fdm-sculpt-filament-id", "fdm-sculpt:filament-id"} or metadata_name.endswith(":filament-id"):
                filament_id = (metadata.text or "").strip() or None
        if filament_id:
            material = Material(material.name, material.color, filament_id)
        base_name = object_element.get("name", f"object-{object_id}")
        occurrence = used_names.get(base_name, 0)
        used_names[base_name] = occurrence + 1
        name = base_name if occurrence == 0 else f"{base_name}-{occurrence + 1}"
        volumes.append(
            ColorVolume(
                name,
                Mesh(vertices, triangles),
                material,
                _parse_transform(build_item.get("transform")),
            )
        )

    manifest: Mapping[str, Any] = {}
    if MANIFEST_PART in names:
        try:
            loaded = json.loads(archive.read(MANIFEST_PART))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FormatError("3MF manifest is invalid JSON") from exc
        if not isinstance(loaded, dict):
            raise FormatError("3MF manifest root must be an object")
        manifest = loaded
    else:
        for metadata in _children(root, "metadata"):
            metadata_name = metadata.get("name", "")
            if metadata_name in {"fdm-sculpt-manifest", "fdm-sculpt:manifest"} or metadata_name.endswith(":manifest"):
                try:
                    loaded = json.loads(metadata.text or "{}")
                except json.JSONDecodeError as exc:
                    raise FormatError("3MF embedded manifest is invalid JSON") from exc
                if isinstance(loaded, dict):
                    manifest = loaded
                break
    return ThreeMFDocument(tuple(volumes), manifest, unit)


def loads_3mf(data: bytes) -> ThreeMFDocument:
    try:
        with ZipFile(BytesIO(data), "r") as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise FormatError(f"3MF contains corrupt ZIP member {bad_member!r}")
            return _read_archive(archive)
    except BadZipFile as exc:
        raise FormatError("3MF is not a readable OPC ZIP package") from exc


def read_3mf(path: str | Path) -> ThreeMFDocument:
    try:
        with ZipFile(Path(path), "r") as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise FormatError(f"3MF contains corrupt ZIP member {bad_member!r}")
            return _read_archive(archive)
    except BadZipFile as exc:
        raise FormatError("3MF is not a readable OPC ZIP package") from exc


# Explicit export/import aliases read naturally at pipeline call sites.
export_3mf = write_3mf
import_3mf = read_3mf
load_stl = read_stl


__all__ = [
    "CORE_NS",
    "ColorVolume",
    "FormatError",
    "Material",
    "Mesh",
    "StlSanitizationResult",
    "ThreeMFDocument",
    "coerce_mesh",
    "dumps_3mf",
    "dumps_ascii_stl",
    "dumps_binary_stl",
    "export_3mf",
    "import_3mf",
    "load_stl",
    "loads_3mf",
    "loads_stl",
    "mesh_hash",
    "normalise_color",
    "read_3mf",
    "read_stl",
    "sanitize_stl_mesh",
    "write_3mf",
    "write_ascii_stl",
    "write_binary_stl",
    "write_stl",
]
