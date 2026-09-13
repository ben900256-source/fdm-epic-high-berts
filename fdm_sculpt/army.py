"""Expand reusable model recipes and unit layouts without generating geometry."""
from copy import deepcopy
import json
from pathlib import Path

from .components.elves_v2 import identity, multiply, translation
from .components.parts import catalog, resolve_assembly, rigid_matrix


def _read(path, stack):
    path = Path(path).resolve()
    if path in stack:
        raise ValueError('Cyclic army recipe: '+str(path))
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1:
        raise ValueError('Invalid army recipe schema')
    return path, data, (*stack, path)


def load_model(path, definitions=None, _stack=()):
    """Inherit a reviewed figure, remove slots, and replace/add pinned pieces."""
    definitions = catalog() if definitions is None else definitions
    path, data, stack = _read(path, _stack)
    source = data['source']
    assembly = load_assembly(path.parent/source['assembly'], definitions, stack)
    prefix = source['figure']+'/'
    origin = source.get('origin_mm', [0, 0, 0])
    if len(origin) != 3:
        raise ValueError('Model origin must have three coordinates')
    offset = rigid_matrix(translation([-v for v in origin]))
    slots = {}
    for p in assembly['placements']:
        if p['instance_id'].startswith(prefix):
            item = deepcopy(p)
            item['instance_id'] = item['instance_id'][len(prefix):]
            item['mount'] = multiply(offset, item['mount'])
            slots[item['instance_id']] = item
    if not slots:
        raise ValueError('Source figure does not exist: '+source['figure'])
    for slot in data.get('remove', []):
        if slot not in slots:
            raise ValueError('Cannot remove unknown model slot: '+slot)
        del slots[slot]
    edits = data.get('parts', [])
    if len({p['instance_id'] for p in edits}) != len(edits):
        raise ValueError('Duplicate model slot override')
    for p in edits:
        if '/' in p['instance_id']:
            raise ValueError('Model slot names cannot contain slashes')
        slots[p['instance_id']] = deepcopy(p)
    return resolve_assembly(dict(schema_version=1, assembly_id=data['model_id'],
                                 placements=list(slots.values())), definitions)


def load_assembly(path, definitions=None, _stack=()):
    """Flatten a layout to the existing pinned placement contract for atelier."""
    definitions = catalog() if definitions is None else definitions
    path, data, stack = _read(path, _stack)
    placements = []
    if 'base_assembly' in data:
        placements = load_assembly(path.parent/data['base_assembly'], definitions, stack)['placements']
    placements.extend(deepcopy(data.get('placements', [])))
    seen = set()
    for instance in data.get('models', []):
        name = instance['instance_id']
        if not name or '/' in name or name in seen:
            raise ValueError('Model instance names must be unique and cannot contain slashes')
        seen.add(name)
        prefix = name+'/'
        existing = [p for p in placements if p['instance_id'].startswith(prefix)]
        if instance.get('replace', False):
            if not existing:
                raise ValueError('Cannot replace unknown model: '+name)
            placements = [p for p in placements if not p['instance_id'].startswith(prefix)]
        elif existing:
            raise ValueError('Model instance already exists: '+name)
        model = load_model(path.parent/instance['model'], definitions, stack)
        mount = rigid_matrix(instance.get('mount', identity()))
        for p in model['placements']:
            placements.append(dict(p, instance_id=prefix+p['instance_id'],
                                   mount=multiply(mount, p['mount'])))
    result = dict(schema_version=1, assembly_id=data['assembly_id'], placements=placements)
    if 'label' in data:
        result['label'] = data['label']
    return resolve_assembly(result, definitions)
