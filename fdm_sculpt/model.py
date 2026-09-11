"""Blender-free JSON records and millimeter transforms."""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping, Self

Vec3 = tuple[float, float, float]


def _vec3(value: Any, field_name: str, *, positive: bool = False) -> Vec3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly three numbers")
    converted = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in converted):
        raise ValueError(f"{field_name} must contain finite numbers")
    if positive and not all(component > 0 for component in converted):
        raise ValueError(f"{field_name} must contain positive numbers")
    return converted  # type: ignore[return-value]


class JsonBacked:
    """Small mixin shared by all persisted specification records."""

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        raise NotImplementedError

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, indent=indent, allow_nan=False
        )

    @classmethod
    def from_json(cls, value: str | bytes | bytearray) -> Self:
        decoded = json.loads(value)
        if not isinstance(decoded, dict):
            raise ValueError(f"{cls.__name__} JSON root must be an object")
        return cls.from_dict(decoded)

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_json() + "\n", encoding="utf-8")
        return destination

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class TransformSpec(JsonBacked):
    """A deterministic transform in Blender's XYZ Euler convention."""

    translate_mm: Vec3 = (0.0, 0.0, 0.0)
    rotate_deg: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "translate_mm", _vec3(self.translate_mm, "translate_mm"))
        object.__setattr__(self, "rotate_deg", _vec3(self.rotate_deg, "rotate_deg"))
        object.__setattr__(self, "scale", _vec3(self.scale, "scale", positive=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "translate_mm": list(self.translate_mm),
            "rotate_deg": list(self.rotate_deg),
            "scale": list(self.scale),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            translate_mm=data.get("translate_mm", (0.0, 0.0, 0.0)),
            rotate_deg=data.get("rotate_deg", (0.0, 0.0, 0.0)),
            scale=data.get("scale", (1.0, 1.0, 1.0)),
        )
