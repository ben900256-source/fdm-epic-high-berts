"""One-time recipe migration; normal part loading never imports whole elves."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.core import ComponentDefinition, component_digest
from fdm_sculpt.components.elves import ELF_V11_DEFINITIONS
from fdm_sculpt.components.elves_v2 import identity, multiply, translation
from fdm_sculpt.components.parts import inverse_rigid, validate_part


def group(role):
    if role.startswith("mail_"):
        return "mail"
    if role in ("helmet_leaf_crest", "helmet_crest_spine"):
        return "crest"
    if role.startswith("helmet_"):
        return "helmet"
    if role in ("cranium", "chin", "nose_plane", "head_envelope", "nose_root",
                "left_eye_socket", "right_eye_socket", "mouth_line"):
        return "head"
    if role.startswith("seahorse_"):
        return "shield-insignia"
    if role in ("shield_ground_heel", "shield_spear_brace"):
        return "equipment-joins"
    if role.startswith("shield"):
        return "shield"
    if role.startswith("spear"):
        return "spear"
    if role.startswith("cape_") or role == "cloak":
        return "cape"
    if role.startswith("skirt_"):
        return "skirt"
    if role in ("torso", "cuirass_lower", "cuirass_upper", "collar"):
        return "torso"
    for side in ("left", "right"):
        if role in (side+"_pauldron", side+"_tunic_hem"):
            return side+"-tunic"
        if role in [side+"_"+s for s in ("sole", "toe", "ankle", "shin", "knee", "thigh", "hip")]:
            return side+"-leg"
        if role.startswith(side+"_"):
            return side+"-arm"
    raise ValueError("unclassified geometry: "+role)


def clean(value):
    if isinstance(value, float):
        return round(value, 9) + 0.0
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def extract():
    definitions, fingerprints, placements = {}, {}, []
    for index, source in enumerate(ELF_V11_DEFINITIONS):
        p = source.to_dict()["parameters"]
        atoms = {a["role"]: a for a in p["atoms"]}
        for family in dict.fromkeys(group(a["role"]) for a in p["atoms"]):
            owned = [a for a in p["atoms"] if group(a["role"]) == family]
            if family in ("head", "helmet", "crest"):
                mount = multiply(p["frames"]["head"], translation([0, 0, 7.2]))
            elif family in ("shield", "shield-insignia"):
                mount = multiply(p["frames"]["shield"], translation([-0.28, -0.99, 3.175]))
            elif family == "spear":
                mount = multiply(p["frames"]["spear"], translation([1.05, -1.22, 6]))
            elif family.endswith("-tunic"):
                mount = atoms[family.split('-')[0]+"_pauldron"]["frame_mm"]
            else:
                mount = multiply(p["frames"]["body"], translation([0, 0, 5.2]))
            inverse = inverse_rigid(mount)
            local = deepcopy(owned)
            for atom in local:
                atom["frame_mm"] = clean(multiply(inverse, atom.get("frame_mm", identity())))
            roles = {a["role"] for a in local}
            operations = [o for o in p["operations"] if o["target"] in roles]
            assert all(o["operand"] in roles for o in operations)
            landmarks = {"mount": [0, 0, 0]}
            for atom in local:
                location = atom.get("location")
                if location is None:
                    location = [(a+b)/2 for a, b in zip(atom["start"], atom["end"])]
                frame = atom["frame_mm"]
                landmarks[atom["role"]] = clean([sum(frame[i][j]*location[j] for j in range(3))+frame[i][3] for i in range(3)])
            parameters = dict(atoms=local, operations=operations, landmarks=landmarks,
                              provenance="parameter recipe extracted from spearman revision 11")
            fingerprint = component_digest(parameters)
            if fingerprint not in fingerprints:
                suffix = "" if not any(d.family == family for d in definitions.values()) else "-"+source.component_id[-1]
                definition = validate_part(ComponentDefinition(
                    component_id="aurelian."+family+suffix, version=1, name=family.replace('-', ' ')+suffix,
                    family=family, required_anchors=("mount",), semantic_slots=("mono",),
                    output_roles=tuple(a["role"] for a in local if a["export"]), parameters=parameters))
                definitions[definition.reference] = definition
                fingerprints[fingerprint] = definition
            definition = fingerprints[fingerprint]
            placements.append(dict(instance_id=f"elf-{index+1:02d}/{family}", part=definition.reference,
                                   definition_sha256=definition.sha256,
                                   mount=clean(multiply(translation([-8+4*index, 0, 1]), mount))))
    base = ComponentDefinition(component_id="aurelian.strip", version=1, name="20 mm strip", family="base",
        required_anchors=("mount",), semantic_slots=("mono",), output_roles=("strip",),
        parameters=dict(atoms=[dict(role="strip", primitive="cube", export=True, dimensions=[20,5,1],
                                   location=[0,0,0.5], bevel=0)], operations=[], landmarks=dict(mount=[0,0,0])))
    definitions[base.reference] = base
    placements.insert(0, dict(instance_id="strip", part=base.reference, definition_sha256=base.sha256, mount=identity()))
    return definitions, dict(schema_version=1, assembly_id="aurelian-spearmen-modular-v1", placements=placements)


if __name__ == "__main__":
    definitions, assembly = extract()
    destination = ROOT/'fdm_sculpt/components/parts'
    destination.mkdir(exist_ok=True)
    for ref, definition in definitions.items():
        path = destination/(ref+'.json')
        if path.exists():
            raise ValueError("migration does not overwrite pinned parts")
        path.write_text(json.dumps(definition.to_dict(), indent=2)+'\n')
    (ROOT/'specs/elf-modular-visual.json').write_text(json.dumps(assembly, indent=2)+'\n')
    (ROOT/'tests/fixtures/parts-v1-golden.json').write_text(json.dumps(
        {ref: d.sha256 for ref, d in definitions.items()}, indent=2)+'\n')
    print(f"Stored {len(definitions)} independent parts for {len(assembly['placements'])} placements")
