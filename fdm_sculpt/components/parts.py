"""Blender-free catalog and assembly contracts for independently owned parts."""
from pathlib import Path
import json
import math

from .core import ComponentDefinition, component_digest
from .elves_v2 import identity, multiply

CATALOG = Path(__file__).with_name("parts")


def rigid_matrix(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 4 or
            any(len(row) != 4 for row in value)):
        raise ValueError("mount must be a 4 by 4 rigid matrix")
    if any(type(x) not in (int, float) or not math.isfinite(x) for row in value for x in row):
        raise ValueError("mount must contain finite numbers")
    if list(value[3]) != [0, 0, 0, 1]:
        raise ValueError("invalid mount bottom row")
    for i in range(3):
        for j in range(3):
            if abs(sum(value[k][i]*value[k][j] for k in range(3)) - (i == j)) > 1e-7:
                raise ValueError("mount may rotate and translate, not scale or shear")
    a = value
    det = (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1]) -
           a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0]) +
           a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
    if abs(det-1) > 1e-7:
        raise ValueError("mount must preserve handedness")
    return [list(row) for row in value]


def inverse_rigid(matrix):
    matrix = rigid_matrix(matrix)
    result = identity()
    for i in range(3):
        for j in range(3):
            result[i][j] = matrix[j][i]
        result[i][3] = -sum(result[i][j]*matrix[j][3] for j in range(3))
    return result


def validate_part(definition):
    p = definition.to_dict()["parameters"]
    atoms = {a["role"]: a for a in p["atoms"]}
    if len(atoms) != len(p["atoms"]):
        raise ValueError("duplicate part geometry role")
    if tuple(a["role"] for a in p["atoms"] if a["export"]) != definition.output_roles:
        raise ValueError("part output roles disagree with its primitives")
    if "mount" not in p["landmarks"]:
        raise ValueError("part needs its own mount landmark")
    for atom in atoms.values():
        if atom["primitive"] not in {"cube", "sphere", "cone", "cylinder", "between"}:
            raise ValueError("unsupported part primitive")
        if "frame_mm" in atom:
            rigid_matrix(atom["frame_mm"])
    for operation in p["operations"]:
        if (operation["solver"] != "EXACT" or operation["operation"] not in {"UNION", "DIFFERENCE", "INTERSECT"}
                or operation["target"] not in atoms or operation["operand"] not in atoms):
            raise ValueError("part must own both operands of each ordered Exact operation")
    return definition


def catalog(root=CATALOG):
    result = {}
    for path in sorted(Path(root).glob("*.json")):
        definition = validate_part(ComponentDefinition.from_dict(json.loads(path.read_text())))
        if definition.reference in result:
            raise ValueError("duplicate part reference")
        result[definition.reference] = definition
    return result


def resolve_assembly(data, definitions=None):
    definitions = catalog() if definitions is None else definitions
    if data.get("schema_version") != 1 or not data.get("assembly_id"):
        raise ValueError("invalid visual assembly schema")
    if not data.get("placements"):
        raise ValueError("assembly needs at least one part")
    seen, placements = set(), []
    for item in data["placements"]:
        name = item["instance_id"]
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError("part instance IDs must be nonempty and unique")
        seen.add(name)
        definition = definitions[item["part"]]
        if item["definition_sha256"] != definition.sha256:
            raise ValueError(f"pinned definition changed: {definition.reference}")
        placements.append(dict(instance_id=name, part=definition.reference,
                               definition_sha256=definition.sha256, mount=rigid_matrix(item["mount"])))
    result = dict(schema_version=1, assembly_id=data["assembly_id"], placements=placements)
    if 'label' in data:
        if not isinstance(data['label'], str) or not data['label'].strip():
            raise ValueError('assembly label must be nonempty text')
        result['label'] = data['label']
    return result


def isolated_part(reference, definitions=None):
    definitions = catalog() if definitions is None else definitions
    definition = definitions[reference]
    return dict(schema_version=1, assembly_id="isolated-"+definition.component_id,
                placements=[dict(instance_id="part", part=reference,
                                 definition_sha256=definition.sha256, mount=identity())])


def cache_key(definition, engine_hash):
    # Placement, assembly seed and unrelated catalog revisions never invalidate
    # an unchanged deterministic part. Engine changes do invalidate its mesh.
    return component_digest(dict(definition=definition.sha256, engine=engine_hash,
                                 blender="5.1.2", format=1))
