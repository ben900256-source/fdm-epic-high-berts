"""Reference-library 3MF export and reopen checks.

The deterministic OPC implementation in :mod:`fdm_sculpt.formats` remains
useful for byte-stable fixtures. Release artifacts pass through the official
Lib3MF bindings so schema and resource mistakes are caught by an independent
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
import uuid

from .formats import ColorVolume, FormatError


METADATA_NAMESPACE = "https://fdm-color-sculpt.invalid/metadata/2026/07"
UUID_NAMESPACE = uuid.UUID("7e1676f6-0af5-52e0-9d02-0e18ccfc8da9")


class Lib3MFUnavailable(RuntimeError):
    """Raised when the optional Lib3MF Python binding is not installed."""


class Lib3MFOperationError(RuntimeError):
    """Raised when Lib3MF rejects a model or artifact."""


def _library() -> Any:
    try:
        import lib3mf
    except (ImportError, OSError) as exc:  # a missing native DLL is also optional
        raise Lib3MFUnavailable(
            "Lib3MF 2.5+ is required for release 3MF export and validation"
        ) from exc
    return lib3mf


def is_available() -> bool:
    try:
        _library().get_wrapper()
    except (Lib3MFUnavailable, Exception):
        return False
    return True


def _position(lib3mf: Any, coordinates: tuple[float, float, float]) -> Any:
    value = lib3mf.Position()
    for axis, coordinate in enumerate(coordinates):
        value.Coordinates[axis] = float(coordinate)
    return value


def _triangle(lib3mf: Any, indices: tuple[int, int, int]) -> Any:
    value = lib3mf.Triangle()
    for axis, index in enumerate(indices):
        value.Indices[axis] = int(index)
    return value


def _transform(lib3mf: Any, values: tuple[float, ...]) -> Any:
    result = lib3mf.Transform()
    for row in range(4):
        for column in range(3):
            result.Fields[row][column] = float(values[row * 3 + column])
    return result


def write_3mf(
    path: str | Path,
    volumes: Iterable[ColorVolume],
    *,
    manifest: Mapping[str, Any] | None = None,
    title: str | None = None,
) -> Path:
    """Write a material 3MF with Lib3MF using millimetre model units."""

    lib3mf = _library()
    wrapper = lib3mf.get_wrapper()
    model = wrapper.CreateModel()
    model.SetUnit(lib3mf.ModelUnit.MilliMeter)
    normalised = tuple(
        item if isinstance(item, ColorVolume) else ColorVolume(**item)  # type: ignore[arg-type]
        for item in volumes
    )
    if not normalised:
        raise FormatError("a Lib3MF document must contain at least one color volume")
    if len({item.name for item in normalised}) != len(normalised):
        raise FormatError("Lib3MF volume names must be unique")

    material_group = model.AddBaseMaterialGroup()
    material_indices: dict[tuple[str, str, str | None], int] = {}
    for volume in normalised:
        material = volume.material
        key = (material.name, material.color, material.filament_id)
        if key in material_indices:
            continue
        rgba = bytes.fromhex(material.color.removeprefix("#"))
        display_color = wrapper.RGBAToColor(*rgba)
        material_indices[key] = int(
            material_group.AddMaterial(material.name, display_color)
        )

    for volume in normalised:
        mesh = model.AddMeshObject()
        mesh.SetName(volume.name)
        mesh.SetUUID(str(uuid.uuid5(UUID_NAMESPACE, f"object:{volume.name}")))
        vertices = [_position(lib3mf, vertex) for vertex in volume.mesh.vertices]
        triangles = [_triangle(lib3mf, face) for face in volume.mesh.triangles]
        mesh.SetGeometry(vertices, triangles)
        material = volume.material
        material_index = material_indices[
            (material.name, material.color, material.filament_id)
        ]
        mesh.SetObjectLevelProperty(
            material_group.GetUniqueResourceID(), material_index
        )
        if material.filament_id:
            mesh.GetMetaDataGroup().AddMetaData(
                METADATA_NAMESPACE,
                "filament-id",
                material.filament_id,
                "xs:string",
                False,
            )
        build_item = model.AddBuildItem(mesh, _transform(lib3mf, volume.transform))
        build_item.SetUUID(
            str(uuid.uuid5(UUID_NAMESPACE, f"build-item:{volume.name}"))
        )

    model.SetBuildUUID(
        str(
            uuid.uuid5(
                UUID_NAMESPACE,
                "build:" + "|".join(volume.name for volume in normalised),
            )
        )
    )

    metadata = model.GetMetaDataGroup()
    if title:
        metadata.AddMetaData(
            "http://purl.org/dc/elements/1.1/", "title", str(title), "xs:string", False
        )
    effective_manifest = dict(manifest or {})
    effective_manifest.setdefault("schema", "fdm-sculpt-manifest-1")
    effective_manifest.setdefault("unit", "millimeter")
    effective_manifest.setdefault("object_count", len(normalised))
    effective_manifest.setdefault(
        "materials",
        [
            {
                "name": material.name,
                "color": material.color,
                **(
                    {"filament_id": material.filament_id}
                    if material.filament_id
                    else {}
                ),
            }
            for material in dict.fromkeys(volume.material for volume in normalised)
        ],
    )
    if effective_manifest:
        payload = json.dumps(
            effective_manifest,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        metadata.AddMetaData(
            METADATA_NAMESPACE,
            "manifest",
            payload,
            "xs:string",
            False,
        )

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        model.QueryWriter("3mf").WriteToFile(str(destination))
    except Exception as exc:
        raise Lib3MFOperationError(f"Lib3MF failed to write {destination}: {exc}") from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise Lib3MFOperationError(f"Lib3MF did not create {destination}")
    return destination


@dataclass(frozen=True, slots=True)
class Lib3MFInspection:
    path: Path
    library_version: str
    unit: str | None
    object_count: int
    build_item_count: int
    material_group_count: int
    material_count: int
    warning_count: int
    expected_object_count: int | None = None
    expected_material_count: int | None = None
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "library_version": self.library_version,
            "unit": self.unit,
            "object_count": self.object_count,
            "build_item_count": self.build_item_count,
            "material_group_count": self.material_group_count,
            "material_count": self.material_count,
            "warning_count": self.warning_count,
            "expected_object_count": self.expected_object_count,
            "expected_material_count": self.expected_material_count,
            "passed": self.passed,
            "errors": list(self.errors),
        }


def inspect_3mf(
    path: str | Path,
    *,
    expected_object_count: int | None = None,
    expected_material_count: int | None = None,
) -> Lib3MFInspection:
    """Reopen a 3MF with Lib3MF and verify units and resource counts."""

    lib3mf = _library()
    wrapper = lib3mf.get_wrapper()
    version = ".".join(str(part) for part in wrapper.GetLibraryVersion())
    model = wrapper.CreateModel()
    reader = model.QueryReader("3mf")
    source = Path(path)
    try:
        reader.ReadFromFile(str(source))
    except Exception as exc:
        raise Lib3MFOperationError(f"Lib3MF failed to read {source}: {exc}") from exc

    unit_value = model.GetUnit()
    unit = "millimeter" if unit_value == lib3mf.ModelUnit.MilliMeter else str(unit_value)
    objects = int(model.GetObjects().Count())
    build_items = int(model.GetBuildItems().Count())
    groups_iterator = model.GetBaseMaterialGroups()
    group_count = int(groups_iterator.Count())
    material_count = 0
    while groups_iterator.MoveNext():
        material_count += int(groups_iterator.GetCurrentBaseMaterialGroup().GetCount())
    warnings = int(reader.GetWarningCount())
    errors: list[str] = []
    if unit != "millimeter":
        errors.append(f"model unit is {unit!r}, expected 'millimeter'")
    if objects <= 0 or build_items <= 0:
        errors.append("3MF contains no printable objects/build items")
    if expected_object_count is not None and objects != expected_object_count:
        errors.append(
            f"object count {objects} does not match expected {expected_object_count}"
        )
    if expected_material_count is not None and material_count != expected_material_count:
        errors.append(
            f"material count {material_count} does not match expected {expected_material_count}"
        )
    return Lib3MFInspection(
        source,
        version,
        unit,
        objects,
        build_items,
        group_count,
        material_count,
        warnings,
        expected_object_count,
        expected_material_count,
        tuple(errors),
    )


__all__ = [
    "Lib3MFInspection",
    "Lib3MFOperationError",
    "Lib3MFUnavailable",
    "METADATA_NAMESPACE",
    "UUID_NAMESPACE",
    "inspect_3mf",
    "is_available",
    "write_3mf",
]
