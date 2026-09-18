import copy
import json
from pathlib import Path
import subprocess

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec, ComponentLibraryError, component_digest
from fdm_sculpt.components.elves import ELF_DEFINITIONS, ELF_LIBRARY, resolve_elf
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec
from fdm_sculpt.prusa import (NOZZLES, TOOL_FIELDS, check_profile, flatten_section,
                              read_settings, resolve_profile)
from fdm_sculpt.regiment_validation import parse_gcode, section_loops, solid_loop_indices
from fdm_sculpt.formats import Mesh, dumps_binary_stl, loads_stl, sanitize_stl_mesh

ROOT = Path(__file__).resolve().parent.parent


def test_spec_roundtrip_and_pinned_placements():
    spec = RegimentSpec.load(ROOT/"specs/elf-spearman-proof.json")
    assert RegimentSpec.from_dict(spec.to_dict()) == spec
    assert [i.component_id[-1] for i in spec.instances] == list("abaca")
    assert [i.anchors["sole"].translate_mm[0] for i in spec.instances] == [-8,-4,0,4,8]
    for field, value in (("strip_mm",[20,5,2]),("seed",True),("printer_profile","x1c-0.4-0.08")):
        data = spec.to_dict()
        data[field] = value
        with pytest.raises(ValueError):
            RegimentSpec.from_dict(data)
    data = spec.to_dict()
    data["placements"][0]["version"] = 999
    with pytest.raises(ComponentLibraryError):
        RegimentSpec.from_dict(data)


@pytest.mark.parametrize("definition",ELF_DEFINITIONS)
def test_elf_definition_resolver_contract(definition):
    instance = ComponentInstanceSpec(definition.component_id,1,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan = resolve_elf(definition,instance)
    golden = json.loads((ROOT/"tests/fixtures/elf-proof-golden.json").read_text())[definition.reference]
    assert definition.sha256 == golden["definition"]
    assert component_digest(plan) == golden["plan"]
    assert plan["sole_to_eye_mm"]==8
    assert plan["helmet_tip_mm"]==9.5
    assert plan["spear_tip_mm"]==12
    assert plan["spear_diameter_mm"]>=1
    assert definition.output_roles == tuple(a["role"] for a in plan["atoms"] if a["export"])
    assert plan["operations"] == [dict(target="shield",operand="shield_lens_mask",operation="INTERSECT",solver="EXACT")]
    for leg in plan["legs"].values():
        assert set(leg)=={"hip","knee","ankle","heel","toe","femur_axis","shin_axis","foot_axis"}
    shifted = ComponentInstanceSpec(definition.component_id,1,"default",{"sole":TransformSpec(translate_mm=(4,0,1))},{"mono":"ivory"})
    resolved = resolve_elf(definition,shifted)
    for local,world in zip(plan["atoms"],resolved["atoms"]):
        key = "start" if "start" in local else "location"
        assert world[key] == pytest.approx([v+t for v,t in zip(local[key],(4,0,1))])
    assert component_digest(plan) != component_digest(resolved)
    for anchors,bindings in (({}, {"mono":"ivory"}), ({"sole":TransformSpec()},{"extra":"ivory"}),
                             ({"sole":TransformSpec(scale=(2,2,2))},{"mono":"ivory"})):
        with pytest.raises(ComponentLibraryError):
            resolve_elf(definition,ComponentInstanceSpec(definition.component_id,1,"bad",anchors,bindings))


def test_elf_recipes_do_not_import_blender():
    text = (ROOT/"fdm_sculpt/components/elves.py").read_text()
    assert "import bpy" not in text and "blender_backend" not in text


def test_profile_inheritance_is_ordered_and_fail_closed():
    sections = {"print:base":{"speed":"20"},"print:detail":{"inherits":"base","speed":"18"},
                "print:user":{"inherits":"base; detail","layers":"0.05"}}
    assert flatten_section(sections,"print:user")=={"speed":"18","layers":"0.05"}
    with pytest.raises(ValueError,match="missing"):
        flatten_section(sections,"print:missing")
    sections["print:base"]["inherits"]="user"
    with pytest.raises(ValueError,match="cycle"):
        flatten_section(sections,"print:user")


def valid_profile():
    return dict(nozzle_diameter="0.4,0.25,0.4,0.4,0.4", min_layer_height="0.05,0.05,0.05,0.05,0.05",
                layer_height="0.05", first_layer_height="0.14", perimeters="3", support_material="0",
                support_material_auto="0", wipe_tower="0", binary_gcode="0", brim_width="6",
                printer_model="XL5",filament_type="PLA",bed_shape="0x0,360x0,360x360,0x360",
                printer_technology="FFF",gcode_flavor="marlin2",**{k:"2" for k in TOOL_FIELDS})


def test_tool_two_compatibility_and_every_adhesion_assignment():
    config = valid_profile()
    check_profile(config)  # The first nozzle is 0.4, the selected one is 0.25.
    for key in TOOL_FIELDS:
        bad = dict(config,**{key:"1"})
        with pytest.raises(ValueError,match="tool 2"):
            check_profile(bad)
    with pytest.raises(ValueError,match="nozzle"):
        check_profile(dict(config,nozzle_diameter="0.25,0.4,0.4,0.4,0.4"))


def test_gcode_verifies_extrusion_not_just_header():
    config = "\n".join(f"; {k} = {v}" for k,v in valid_profile().items())
    text = "; generated by PrusaSlicer 2.9.6\nM83\nT1\n;LAYER_CHANGE\n;Z:0.14\n;TYPE:Skirt/Brim\nG1 X180 Y180\nG1 X181 E0.2\n;LAYER_CHANGE\n;Z:0.19\n;TYPE:External perimeter\nG1 Y181 E0.2\n"+config
    layers,record = parse_gcode(text)
    assert record["extrusion_tools"]==[1] and len(layers)==2
    for broken in (text.replace("T1","T0"), text.replace(";Z:0.19",";Z:0.22"), text.replace("External perimeter","Support material")):
        with pytest.raises(ValueError):
            parse_gcode(broken)


def test_layer_intersection_does_not_hide_missing_faces():
    # A missing side leaves an open contour and must not be silently repaired.
    mesh = Mesh([(0,0,0),(1,0,0),(1,0,1),(0,0,1)],[(0,1,2),(0,2,3)])
    with pytest.raises((ValueError,KeyError)):
        section_loops(mesh,0.5)


def test_layer_void_is_not_a_disappearing_solid():
    loops = [[(0,0),(10,0),(10,10),(0,10)],[(2,2),(4,2),(4,4),(2,4)],
             [(2.5,2.5),(3,2.5),(3,3),(2.5,3)]]
    assert solid_loop_indices(loops)==[0,2]


def test_stl_topology_uses_exact_shared_corners_without_face_removal():
    from fdm_sculpt.validation import analyze_mesh
    tetra = Mesh([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(1,2,3),(2,0,3)])
    raw = loads_stl(dumps_binary_stl(tetra))
    indexed = sanitize_stl_mesh(raw)
    assert indexed.removed_triangle_count==0
    analysis = analyze_mesh(indexed.mesh)
    assert analysis.connected_components==1
    assert analysis.watertight and analysis.manifold and analysis.outward_facing


@pytest.mark.integration
def test_installed_prusa_profile_snapshot(tmp_path):
    import os
    datadir = Path(os.environ.get("APPDATA",""))/"PrusaSlicer"
    if not datadir.exists():
        pytest.skip("installed miniature profiles unavailable")
    ini = resolve_profile(tmp_path, datadir)
    check_profile(read_settings(ini.read_text()))
    evidence = json.loads((tmp_path/"profile-manifest.json").read_text())
    assert len(evidence["inputs"])==3
    assert evidence["selected_tool"]==2


@pytest.mark.integration
def test_saved_elf_blender_provenance(tmp_path):
    import os
    from fdm_sculpt.review import find_blender
    # Tests can verify the delivered full build instead of regenerating hundreds
    # of booleans merely to check properties already tested by each build.
    build = os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a generated proof directory")
    build = Path(build).resolve()
    entry = ROOT/"fdm_sculpt/regiment_provenance_entry.py"
    process = subprocess.run([str(find_blender()),"--background",str(build/"internal/elf-spearman-proof.blend"),
                              "--python-exit-code","1","--python",str(entry),"--",str(build)],
                             capture_output=True,text=True,timeout=120)
    assert process.returncode==0, process.stdout+process.stderr
    record = json.loads((build/"internal/saved-provenance.json").read_text())
    assert record["passes"]
    assert len(record["instances"])==5
