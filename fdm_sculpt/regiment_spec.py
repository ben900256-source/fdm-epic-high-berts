"""Strict specification for the five-figure single-material proof milestone."""
from dataclasses import dataclass
import json
from pathlib import Path

from .components.core import ComponentInstanceSpec
from .components.elves import ELF_LIBRARY, resolve_elf
from .model import TransformSpec


@dataclass(frozen=True)
class RegimentSpec:
    regiment_id: str
    seed: int
    strip_mm: tuple[float, float, float]
    sole_to_eye_mm: float
    printer_profile: str
    instances: tuple[ComponentInstanceSpec, ...]

    @classmethod
    def from_dict(cls, data):
        required = {"schema_version", "regiment_id", "seed", "strip_mm", "sole_to_eye_mm", "printer_profile", "placements"}
        if set(data) != required or data["schema_version"] != 1:
            raise ValueError("invalid RegimentSpec fields/schema version")
        if type(data["seed"]) is not int:
            raise ValueError("seed must be an explicit integer")
        if data["regiment_id"] != "aurelian-leafguard-proof":
            raise ValueError("unknown regiment")
        if tuple(data["strip_mm"]) != (20, 5, 1) or data["sole_to_eye_mm"] != 8:
            raise ValueError("proof requires 20 x 5 x 1 mm strip and 8 mm sole-to-eye")
        if data["printer_profile"] != "prusa-xl-0.25-0.05":
            raise ValueError("proof requires prusa-xl-0.25-0.05")
        placements = data["placements"]
        if len(placements) != 5:
            raise ValueError("proof requires five figures")
        instances = []
        individual_poses = any(all(p.get("version")==v for p in placements) for v in (2,3,4,5,6,7,8,9,10))
        sequence = "abcde" if individual_poses else "abaca"
        for index, (placement, pose) in enumerate(zip(placements, sequence)):
            if set(placement) != {"component_id", "version", "instance_id", "x_mm"}:
                raise ValueError("invalid placement fields")
            if placement["x_mm"] != -8+index*4 or placement["component_id"] != f"aurelian.spearman.{pose}":
                raise ValueError("proof requires pinned ABACA v1 or ABCDE v2/v3/v4/v5/v6/v7/v8/v9/v10 at 4 mm spacing")
            instance = ComponentInstanceSpec(
                placement["component_id"], placement["version"], placement["instance_id"],
                {"sole": TransformSpec(translate_mm=(placement["x_mm"], 0, 1))}, {"mono": "ivory"})
            resolve_elf(ELF_LIBRARY.resolve(instance.component_id, instance.version), instance)
            instances.append(instance)
        if len({i.instance_id for i in instances}) != 5:
            raise ValueError("instance IDs must be unique")
        return cls(data["regiment_id"], data["seed"], tuple(data["strip_mm"]),
                   data["sole_to_eye_mm"], data["printer_profile"], tuple(instances))

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self):
        return dict(schema_version=1, regiment_id=self.regiment_id, seed=self.seed,
                    strip_mm=list(self.strip_mm), sole_to_eye_mm=self.sole_to_eye_mm,
                    printer_profile=self.printer_profile,
                    placements=[dict(component_id=i.component_id, version=i.version,
                                     instance_id=i.instance_id, x_mm=i.anchors["sole"].translate_mm[0])
                                for i in self.instances])
