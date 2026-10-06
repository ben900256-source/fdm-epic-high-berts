"""Repeatable support diagnostics for current army exports, without validation claims."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from . import prusa
from .printability import assess_toolpaths


PROFILE_KEYS = (
    *prusa.TOOL_FIELDS, 'nozzle_diameter', 'printer_model', 'printer_technology',
    'layer_height', 'first_layer_height', 'temperature', 'first_layer_temperature',
    'filament_type', 'filament_settings_id', 'printer_settings_id', 'print_settings_id',
    'complete_objects', 'support_material', 'support_material_auto', 'wipe_tower',
    'min_print_speed', 'slowdown_below_layer_time', 'binary_gcode', 'arc_fitting',
    'external_perimeter_extrusion_width', 'external_perimeter_acceleration',
)


def check_diagnostic_profile(actual, expected):
    """Bind the slice to its freshly resolved preset, preserving historical gates."""
    fixed = dict(nozzle_diameter='0.4,0.25,0.4,0.4,0.4', printer_model='XL5IS',
                 printer_technology='FFF', layer_height='0.05', first_layer_height='0.14',
                 support_material='0', support_material_auto='0', wipe_tower='0',
                 complete_objects='0', binary_gcode='0', arc_fitting='disabled')
    fixed.update({key: '2' for key in prusa.TOOL_FIELDS})
    for key, value in fixed.items():
        if expected.get(key) != value:
            raise ValueError(f'diagnostic profile requires {key}={value}')
    if set(expected['filament_type'].split(';')) != {'PLA'}:
        raise ValueError('diagnostic requires PLA')
    for key in PROFILE_KEYS:
        if key not in expected or actual.get(key) != expected[key]:
            raise ValueError(f'slice disagrees with resolved profile: {key}')
    # Check every other serialized execution setting as well; IDs and compatibility
    # metadata may be omitted by PrusaSlicer, but changed saved values are rejected.
    for key in actual.keys() & expected.keys():
        if actual[key] != expected[key]:
            raise ValueError(f'slice changed saved setting: {key}')


def automatic_support_audit(output, job, config):
    folder = output / 'support-audit'
    folder.mkdir(exist_ok=True)
    diagnostic = dict(config)
    diagnostic.update(support_material='1', support_material_auto='1',
                      support_material_threshold='45', support_material_style='organic',
                      support_material_buildplate_only='0')
    ini = folder / 'diagnostic.ini'
    ini.write_text(''.join(f'{k} = {v}\n' for k, v in sorted(diagnostic.items())), encoding='utf-8')
    # Retain object placement and tool assignment; only the support options differ.
    project = folder / 'diagnostic-supports.3mf'
    with ZipFile(output / job['project']) as source, ZipFile(project, 'w', ZIP_DEFLATED) as target:
        for name in source.namelist():
            if name != 'Metadata/Slic3r_PE.config':
                target.writestr(name, source.read(name))
        target.writestr('Metadata/Slic3r_PE.config',
                        ''.join(f'; {k} = {v}\n' for k, v in sorted(diagnostic.items())))
    gcode = folder / 'diagnostic-supports.gcode'
    isolated = folder / 'isolated-settings'
    isolated.mkdir(exist_ok=True)
    execution = prusa.run_slicer(
        [prusa.EXECUTABLE, '--datadir', isolated, '--threads', '2', '--loglevel', '3',
         '--export-gcode', '--output', gcode, project], folder / 'slice.log', gcode,
        ['Slicing process finished', 'Exporting G-code finished', 'Slicing result exported to'])
    text = gcode.read_text(encoding='utf-8')
    actual = prusa.read_settings(text)
    for key in PROFILE_KEYS + ('support_material_threshold', 'support_material_style',
                               'support_material_buildplate_only'):
        if actual.get(key) != diagnostic[key]:
            raise ValueError(f'support diagnostic profile mismatch: {key}')
    lengths = prusa.filament_by_role(text)
    result = dict(label='automatic-support diagnostic; not approved print G-code',
                  support_threshold_degrees_from_bed=45, style='organic',
                  filament_length_mm={k: round(v, 4) for k, v in lengths.items()},
                  support_to_model_filament_ratio=lengths['support']/lengths['model'],
                  zero_support_target_met=lengths['support'] == 0,
                  limitation='conservative estimate; inspect contact locations and removal access',
                  source_project_sha256=job['hashes']['project'],
                  configuration_sha256=prusa.sha256(ini), project_sha256=prusa.sha256(project),
                  execution=execution)
    (folder / 'support-audit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


def assess(output, *, automatic_supports=False):
    from .regiment_validation import parse_gcode
    output = Path(output).resolve()
    job = json.loads((output / 'slicer-overhang-job.json').read_text(encoding='utf-8'))
    if job.get('schema_version') != 1 or job.get('mode') != 'slicer-overhang-diagnostic':
        raise ValueError('unsupported overhang diagnostic manifest')
    for key in ('stl', 'project', 'gcode', 'settings'):
        if prusa.sha256(output / job[key]) != job['hashes'][key]:
            raise ValueError(f'diagnostic input hash mismatch: {key}')
    manifest = json.loads((output / job['profile_manifest']).read_text(encoding='utf-8'))
    if manifest['settings_sha256'] != job['hashes']['settings']:
        raise ValueError('resolved settings do not match profile manifest')
    if not all(prusa.sha256(p['path']) == p['sha256'] for p in manifest['inputs']):
        raise ValueError('installed presets changed since resolution')
    expected = prusa.read_settings((output / job['settings']).read_text(encoding='utf-8'))
    layers, gcode = parse_gcode((output / job['gcode']).read_text(encoding='utf-8'),
        profile_validator=lambda config: check_diagnostic_profile(config, expected), record_layer_gaps=True)
    support = assess_toolpaths(layers, output / 'previews')
    result = dict(label='sliced overhang diagnostic; unchecked Blender export; physical trial pending',
                  digitally_validated=False, scope='deposited toolpaths and optional automatic supports only',
                  name=job['name'], passes=support['passes'] and gcode['continuous_layers'], deposited_layer_support=support['passes'],
                  gcode=gcode, support_summary=support['summary'], criteria=support['criteria'],
                  raster=support['raster'], artifact_sha256=job['hashes'],
                  analysis_source_sha256={name: prusa.sha256(Path(__file__).parent / name)
                      for name in ('slicer_overhang.py', 'regiment_validation.py', 'printability.py', 'prusa.py')})
    if automatic_supports:
        result['automatic_support_audit'] = automatic_support_audit(output, job, expected)
    if not all(prusa.sha256(p['path']) == p['sha256'] for p in manifest['inputs']):
        raise ValueError('installed presets changed during assessment')
    result['installed_profiles_unchanged'] = True
    path = output / 'printability-review.json'
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return dict(passes=result['passes'], label=result['label'],
                support_summary=result['support_summary'], report=str(path))
