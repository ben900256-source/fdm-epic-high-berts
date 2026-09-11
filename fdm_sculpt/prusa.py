"""PrusaSlicer 2.9.5 proof adapter; installed presets are read-only inputs."""
from __future__ import annotations

import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

PROFILE = "prusa-xl-0.25-0.05"
PRINTER = "Original Prusa XL - 5T 0.25 nozzle - Miniatures"
PRINT = "0.05mm ULTRADETAIL @XLIS 0.25 - Balanced Miniatures"
FILAMENT = "Generic PLA @XL"
EXECUTABLE = Path("C:/Program Files/Prusa3D/PrusaSlicer/prusa-slicer-console.exe")
NOZZLES = [0.4, 0.25, 0.4, 0.4, 0.4]
TOOL_FIELDS = ("perimeter_extruder", "infill_extruder", "solid_infill_extruder",
               "support_material_extruder", "support_material_interface_extruder")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_settings(text):
    result = {}
    for line in text.splitlines():
        if line.startswith("; "):
            line = line[2:]
        if not line.strip() or line.lstrip().startswith(("#", ";", "[")) or " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        result[key.strip()] = value.strip()
    return result


def flatten_section(sections, name, stack=()):
    if name in stack:
        raise ValueError(f"preset inheritance cycle: {stack + (name,)}")
    if name not in sections:
        raise ValueError(f"missing inherited preset: {name}")
    current = sections[name]
    resolved = {}
    category = name.split(":", 1)[0]
    for parent in current.get("inherits", "").split(";"):
        if parent.strip():
            resolved.update(flatten_section(sections, category+":"+parent.strip(), stack+(name,)))
    resolved.update({k:v for k,v in current.items() if k != "inherits"})
    return resolved


def check_profile(config):
    if [float(v) for v in config["nozzle_diameter"].split(",")] != NOZZLES:
        raise ValueError("saved nozzle configuration must remain 0.4,0.25,0.4,0.4,0.4")
    for field in TOOL_FIELDS:
        if config.get(field) != "2":
            raise ValueError(f"{field} must select tool 2")
    expected = dict(layer_height="0.05", first_layer_height="0.14", perimeters="3",
                    support_material="0", support_material_auto="0", wipe_tower="0",
                    binary_gcode="0", brim_width="6", printer_model="XL5",
                    filament_type="PLA", bed_shape="0x0,360x0,360x360,0x360",
                    printer_technology="FFF", gcode_flavor="marlin2")
    for key,value in expected.items():
        actual = config.get(key, "")
        if key == "filament_type":
            if set(actual.split(";")) != {"PLA"}:
                raise ValueError("proof requires PLA")
        elif actual != value:
            raise ValueError(f"{key}: expected {value!r}, got {actual!r}")
    if float(config["min_layer_height"].split(",")[1]) > 0.05:
        raise ValueError("selected tool 2 minimum layer height exceeds 0.05 mm")


def resolve_profile(output, datadir=None):
    datadir = Path(datadir or Path(os.environ["APPDATA"])/"PrusaSlicer")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    vendor = datadir / "vendor" / "PrusaResearch.ini"
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str
    parser.read_string(vendor.read_text(encoding="utf-8-sig"))
    sections = {name: dict(parser[name]) for name in parser.sections()}
    inputs = [vendor]
    for category, name in (("print", PRINT), ("printer", PRINTER)):
        path = datadir / category / (name+".ini")
        sections[category+":"+name] = read_settings(path.read_text(encoding="utf-8-sig"))
        inputs.append(path)
    resolved = {}
    for category,name in (("printer", PRINTER), ("print", PRINT), ("filament", FILAMENT)):
        values = flatten_section(sections, category+":"+name)
        (output/(category+"-resolved.json")).write_text(json.dumps(values, sort_keys=True, indent=2)+"\n")
        resolved.update(values)
    # None of the installed printer's tool macros or speeds are replaced.
    resolved.update({key: "2" for key in TOOL_FIELDS})
    resolved.update(dict(support_material="0", support_material_auto="0", wipe_tower="0",
                         binary_gcode="0", gcode_comments="1", arc_fitting="disabled",
                         printer_settings_id=PRINTER, print_settings_id=PROFILE,
                         filament_settings_id=";".join([FILAMENT]*5),
                         compatible_printers_condition="printer_model==\"XL5\" and nozzle_diameter[1]==0.25",
                         compatible_prints_condition="", thumbnails="", post_process=""))
    check_profile(resolved)
    ini = output / (PROFILE+".ini")
    ini.write_text("# Build-local resolved PrusaSlicer proof settings\n"+
                   "".join(f"{k} = {v}\n" for k,v in sorted(resolved.items())), encoding="utf-8")
    input_records = []
    for index,path in enumerate(sorted(inputs)):
        snapshot = output / f"input-{index}-{path.name}"
        snapshot.write_bytes(path.read_bytes())
        input_records.append(dict(source=str(path), snapshot=snapshot.name, sha256=sha256(snapshot)))
    record = dict(profile=PROFILE, selected_tool=2, selected_nozzle_mm=NOZZLES[1],
                  settings_sha256=sha256(ini), inputs=input_records,
                  resolved_hashes={p.name:sha256(p) for p in sorted(output.glob("*-resolved.json"))})
    (output/"profile-manifest.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    return ini


def run_slicer(command, log, artifact, marker):
    if artifact.exists():
        raise ValueError(f"refusing stale slicer artifact: {artifact}")
    started = time.time()
    process = subprocess.run([str(v) for v in command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", timeout=600)
    log.write_text(process.stdout, encoding="utf-8")
    markers = [marker] if isinstance(marker,str) else list(marker)
    if process.returncode or not all(m.lower() in process.stdout.lower() for m in markers):
        raise RuntimeError(f"PrusaSlicer failed or missed {marker!r}; see {log}")
    if not artifact.is_file() or artifact.stat().st_size < 100 or artifact.stat().st_mtime < started-2:
        raise RuntimeError(f"PrusaSlicer did not create a fresh artifact: {artifact}")
    return dict(command=[str(v) for v in command], exit_code=process.returncode,
                marker=marker, artifact_sha256=sha256(artifact), log_sha256=sha256(log))


def inspect_project(path):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("corrupt project archive")
        config = read_settings(archive.read("Metadata/Slic3r_PE.config").decode("utf-8"))
        check_profile(config)
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
        meshes = model.findall(".//m:mesh",ns)
        items = model.findall("m:build/m:item",ns)
        if model.get("unit", "millimeter") != "millimeter" or len(meshes) != 1 or len(items) != 1:
            raise ValueError("project must contain one millimetre strip on one bed")
        model_config = ET.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
        assignments = [m.get("value") for m in model_config.iter("metadata") if m.get("key") == "extruder"]
        if not assignments or any(v != "2" for v in assignments):
            raise ValueError(f"project object tool override mismatch: {assignments}")
        return dict(readable=True, mesh_objects=1, build_items=1,
                    object_tool_overrides=assignments, tool=2, nozzle_mm=0.25, layer_mm=0.05,
                    printer_model=config["printer_model"], config=config)


def assemble_project(geometry, normalized_ini, destination, thumbnail=None):
    """CLI 2.9.5 exports geometry without config; add its saved resolved config.

    The second slicer invocation must consume this archive without --load.
    No mesh coordinates or printer macros are changed here.
    """
    if destination.exists():
        raise ValueError(f"refusing stale project: {destination}")
    config = read_settings(normalized_ini.read_text(encoding="utf-8"))
    check_profile(config)
    payload = "\n".join(f"; {k} = {v}" for k,v in sorted(config.items()))+"\n"
    with ZipFile(geometry) as source, ZipFile(destination,"w",ZIP_DEFLATED) as target:
        for name in sorted(source.namelist()):
            data = source.read(name)
            if name == "[Content_Types].xml":
                root = ET.fromstring(data)
                ns = "{http://schemas.openxmlformats.org/package/2006/content-types}"
                if not any(e.get("Extension")=="png" for e in root):
                    ET.SubElement(root,ns+"Default",dict(Extension="png",ContentType="image/png"))
                data = ET.tostring(root,encoding="utf-8",xml_declaration=True)
            if name == "Metadata/Slic3r_PE_model.config":
                root = ET.fromstring(data)
                for obj in root.findall("object"):
                    ET.SubElement(obj,"metadata",dict(type="object",key="extruder",value="2"))
                    for volume in obj.findall("volume"):
                        ET.SubElement(volume,"metadata",dict(type="volume",key="extruder",value="2"))
                data = ET.tostring(root,encoding="utf-8",xml_declaration=True)
            target.writestr(name,data)
        target.writestr("Metadata/Slic3r_PE.config",payload)
        if thumbnail is not None and thumbnail.exists():
            target.writestr("Metadata/thumbnail.png",thumbnail.read_bytes())


def slice_build(output, executable=EXECUTABLE):
    output = Path(output).resolve()
    folder = output / "prusa"
    folder.mkdir(exist_ok=True)
    version = subprocess.run([str(executable), "--help"], capture_output=True, text=True, timeout=30)
    if "PrusaSlicer-2.9.5 " not in version.stdout:
        raise ValueError("PrusaSlicer 2.9.5 is required")
    ini = resolve_profile(folder/"profile")
    project = output/"elf-spearman-proof-prusa.3mf"
    geometry = folder/"assembled.3mf"
    normalized = folder/"normalized.ini"
    gcode = output/"elf-spearman-proof.gcode"
    isolated = folder/"isolated-settings"
    isolated.mkdir(exist_ok=True)
    common = [executable, "--datadir", isolated, "--threads", "2", "--loglevel", "3"]
    build_record = run_slicer(common + ["--load", ini, "--save", normalized, "--center", "180,180", "--export-3mf",
                             "--output", geometry, output/"elf-spearman-proof.stl"],
                             folder/"project.log", geometry, "File exported to")
    assemble_project(geometry,normalized,project,output/"previews/three-quarter.png")
    build_record["geometry_archive_sha256"] = build_record["artifact_sha256"]
    build_record["artifact_sha256"] = sha256(project)
    build_record["normalized_ini_sha256"] = sha256(normalized)
    build_record["project_method"] = "CLI-exported geometry plus CLI-saved settings and explicit tool-2 object/volume assignment"
    project_record = inspect_project(project)
    # Reopen the project without --load, proving the settings survive export.
    slice_record = run_slicer(common + ["--export-gcode", "--output", gcode, project],
                             folder/"slice.log", gcode,
                             ["Slicing process finished", "Exporting G-code finished", "Slicing result exported to"])
    record = dict(version="2.9.5", export=build_record, reopen_slice=slice_record,
                  project={k:v for k,v in project_record.items() if k != "config"})
    profile_record = json.loads((folder/"profile/profile-manifest.json").read_text())
    record["installed_inputs_unchanged"] = all(sha256(p["source"])==p["sha256"] for p in profile_record["inputs"])
    if not record["installed_inputs_unchanged"]:
        raise RuntimeError("installed preset input changed during the build")
    (folder/"slicer-evidence.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    return record
