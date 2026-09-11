"""Versioned contracts for reusable parametric miniature components.

Component definitions and placements deliberately contain no Blender types.
Assemblies provide named local anchor transforms and semantic bindings; a
registered recipe owns every shape parameter and turns that placement into
procedural geometry through a small duck-typed builder boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Callable, Mapping

from ..model import JsonBacked, TransformSpec


_COMPONENT_ID = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class ComponentLibraryError(ValueError):
    """Raised when a component definition, placement, or lookup is invalid."""


def canonical_component_json(value: Any) -> str:
    """Return the stable JSON representation used for component digests."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def component_digest(value: JsonBacked | Mapping[str, Any]) -> str:
    """Hash a JSON-backed component record without Blender or filesystem state."""

    payload = value.to_dict() if isinstance(value, JsonBacked) else dict(value)
    return hashlib.sha256(canonical_component_json(payload).encode("ascii")).hexdigest()


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComponentLibraryError(f"{field_name} must be a non-empty string")
    return value


def _unique_strings(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_nonempty(value, field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ComponentLibraryError(f"{field_name} entries must be unique")
    return normalized


def _json_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(
            json.dumps(dict(value), sort_keys=True, allow_nan=False)
        )
    except (TypeError, ValueError) as exc:
        raise ComponentLibraryError("component parameters must be JSON-compatible") from exc


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class ComponentDefinition(JsonBacked):
    """Immutable identity and shape contract for one component revision."""

    component_id: str
    version: int
    name: str
    family: str
    required_anchors: tuple[str, ...]
    semantic_slots: tuple[str, ...]
    output_roles: tuple[str, ...]
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not _COMPONENT_ID.fullmatch(self.component_id):
            raise ComponentLibraryError(
                "component_id must be a lowercase dotted or hyphenated identifier"
            )
        if type(self.version) is not int or self.version < 1:
            raise ComponentLibraryError("component version must be a positive integer")
        _nonempty(self.name, "component name")
        _nonempty(self.family, "component family")
        object.__setattr__(
            self,
            "required_anchors",
            _unique_strings(tuple(self.required_anchors), "required anchor"),
        )
        object.__setattr__(
            self,
            "semantic_slots",
            _unique_strings(tuple(self.semantic_slots), "semantic slot"),
        )
        object.__setattr__(
            self,
            "output_roles",
            _unique_strings(tuple(self.output_roles), "output role"),
        )
        if not self.required_anchors:
            raise ComponentLibraryError("component definitions require at least one anchor")
        if not self.semantic_slots:
            raise ComponentLibraryError("component definitions require at least one semantic slot")
        if not self.output_roles:
            raise ComponentLibraryError("component definitions require at least one output role")
        object.__setattr__(self, "parameters", _freeze_json(_json_copy(self.parameters)))

    @property
    def reference(self) -> str:
        return f"{self.component_id}@{self.version}"

    @property
    def sha256(self) -> str:
        return component_digest(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "version": self.version,
            "name": self.name,
            "family": self.family,
            "required_anchors": list(self.required_anchors),
            "semantic_slots": list(self.semantic_slots),
            "output_roles": list(self.output_roles),
            "parameters": _thaw_json(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ComponentDefinition":
        return cls(
            component_id=str(data["component_id"]),
            version=data["version"],
            name=str(data["name"]),
            family=str(data["family"]),
            required_anchors=tuple(str(value) for value in data["required_anchors"]),
            semantic_slots=tuple(str(value) for value in data["semantic_slots"]),
            output_roles=tuple(str(value) for value in data["output_roles"]),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass(frozen=True, slots=True)
class ComponentInstanceSpec(JsonBacked):
    """One explicitly pinned component placement in assembly-local space."""

    component_id: str
    version: int
    instance_id: str
    anchors: Mapping[str, TransformSpec]
    semantic_bindings: Mapping[str, str]

    def __post_init__(self) -> None:
        if not _COMPONENT_ID.fullmatch(self.component_id):
            raise ComponentLibraryError("invalid component_id on instance")
        if type(self.version) is not int or self.version < 1:
            raise ComponentLibraryError("component instance version must be positive")
        _nonempty(self.instance_id, "component instance_id")

        anchors: dict[str, TransformSpec] = {}
        for name, transform in dict(self.anchors).items():
            anchor_name = _nonempty(str(name), "anchor name")
            if anchor_name in anchors:
                raise ComponentLibraryError(f"duplicate anchor {anchor_name!r}")
            if not isinstance(transform, TransformSpec):
                if not isinstance(transform, Mapping):
                    raise ComponentLibraryError(
                        f"anchor {anchor_name!r} must be a TransformSpec or object"
                    )
                transform = TransformSpec.from_dict(transform)
            anchors[anchor_name] = transform
        object.__setattr__(self, "anchors", MappingProxyType(anchors))

        bindings: dict[str, str] = {}
        for slot, semantic in dict(self.semantic_bindings).items():
            slot_name = _nonempty(str(slot), "semantic slot")
            bindings[slot_name] = _nonempty(str(semantic), "semantic binding")
        object.__setattr__(self, "semantic_bindings", MappingProxyType(bindings))

    @property
    def reference(self) -> str:
        return f"{self.component_id}@{self.version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "version": self.version,
            "instance_id": self.instance_id,
            "anchors": {
                name: self.anchors[name].to_dict() for name in sorted(self.anchors)
            },
            "semantic_bindings": {
                slot: self.semantic_bindings[slot]
                for slot in sorted(self.semantic_bindings)
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ComponentInstanceSpec":
        raw_anchors = data.get("anchors", {})
        raw_bindings = data.get("semantic_bindings", {})
        if not isinstance(raw_anchors, Mapping):
            raise ComponentLibraryError("component anchors must be an object")
        if not isinstance(raw_bindings, Mapping):
            raise ComponentLibraryError("semantic_bindings must be an object")
        return cls(
            component_id=str(data["component_id"]),
            version=data["version"],
            instance_id=str(data["instance_id"]),
            anchors={
                str(name): TransformSpec.from_dict(transform)
                for name, transform in raw_anchors.items()
            },
            semantic_bindings={
                str(slot): str(semantic) for slot, semantic in raw_bindings.items()
            },
        )


@dataclass(frozen=True, slots=True)
class ComponentBuildResult:
    """Objects emitted by one component recipe, keyed by stable local role."""

    definition: ComponentDefinition
    instance: ComponentInstanceSpec
    objects: tuple[tuple[str, Any], ...]
    resolved_plan_sha256: str

    def __post_init__(self) -> None:
        roles = tuple(role for role, _obj in self.objects)
        if roles != self.definition.output_roles:
            raise ComponentLibraryError(
                f"{self.definition.reference} emitted roles {roles!r}; "
                f"expected {self.definition.output_roles!r}"
            )
        if len(self.resolved_plan_sha256) != 64:
            raise ComponentLibraryError("resolved plan digest must be SHA-256")

    def object_for(self, role: str) -> Any:
        for candidate, obj in self.objects:
            if candidate == role:
                return obj
        raise KeyError(role)


ComponentFactory = Callable[
    [Any, ComponentDefinition, ComponentInstanceSpec], ComponentBuildResult
]


class ComponentLibrary:
    """Deterministic registry that requires every component version to be pinned."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, int], tuple[ComponentDefinition, ComponentFactory]] = {}
        self._frozen = False

    def register(
        self, definition: ComponentDefinition, factory: ComponentFactory
    ) -> None:
        if self._frozen:
            raise ComponentLibraryError("component library is frozen")
        key = (definition.component_id, definition.version)
        if key in self._entries:
            raise ComponentLibraryError(
                f"duplicate component registration: {definition.reference}"
            )
        self._entries[key] = (definition, factory)

    def freeze(self) -> None:
        """Prevent later registration from changing a production registry."""

        self._frozen = True

    def resolve(self, component_id: str, version: int) -> ComponentDefinition:
        if type(version) is not int or version < 1:
            raise ComponentLibraryError("component version must be a positive integer")
        key = (str(component_id), version)
        try:
            return self._entries[key][0]
        except KeyError as exc:
            raise ComponentLibraryError(
                f"component revision is not registered: {component_id}@{version}"
            ) from exc

    def definitions(self) -> tuple[ComponentDefinition, ...]:
        return tuple(self._entries[key][0] for key in sorted(self._entries))

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "components": [definition.to_dict() for definition in self.definitions()],
        }

    def build(self, builder: Any, instance: ComponentInstanceSpec) -> ComponentBuildResult:
        key = (instance.component_id, instance.version)
        try:
            definition, factory = self._entries[key]
        except KeyError as exc:
            raise ComponentLibraryError(
                f"component revision is not registered: {instance.reference}"
            ) from exc

        actual_anchors = set(instance.anchors)
        expected_anchors = set(definition.required_anchors)
        if actual_anchors != expected_anchors:
            missing = sorted(expected_anchors - actual_anchors)
            extra = sorted(actual_anchors - expected_anchors)
            raise ComponentLibraryError(
                f"{instance.reference} anchor mismatch; missing={missing}, extra={extra}"
            )
        actual_slots = set(instance.semantic_bindings)
        expected_slots = set(definition.semantic_slots)
        if actual_slots != expected_slots:
            missing = sorted(expected_slots - actual_slots)
            extra = sorted(actual_slots - expected_slots)
            raise ComponentLibraryError(
                f"{instance.reference} semantic slot mismatch; "
                f"missing={missing}, extra={extra}"
            )

        result = factory(builder, definition, instance)
        if result.definition != definition or result.instance != instance:
            raise ComponentLibraryError(
                f"{instance.reference} factory returned mismatched provenance"
            )
        return result
