"""Primitive fillers for sealed voids; reviewed chainmail links stay unchanged."""
import json
from pathlib import Path
from .core import ComponentDefinition
from .parts import validate_part


def spearman_join_fill(*, seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    preset = json.loads(Path(__file__).with_name('spearman_join_fill_v1.json').read_text())
    atoms = [dict(role=f'internal_join_void_{index:03}', primitive='cube', export=True,
                  location=[0,0,0], dimensions=box['dimensions'], frame_mm=box['frame_mm'], bevel=0)
             for index, box in enumerate(preset['boxes'])]
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.spearman-join-fill', version=1,
        name='Sealed internal spearman join void fill', family='manufacturing-internal-fill',
        required_anchors=['mount'], semantic_slots=['mono'], output_roles=[a['role'] for a in atoms],
        parameters=dict(seed=seed, atoms=atoms, operations=[], landmarks={'mount':[0,0,0]},
                        source_assembly_sha256=preset['source_assembly_sha256'],
                        design='Three primitive boxes entirely inside the first spearman exterior; use only with its pinned pose.'))))


def mail_internal_fill(*, seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    preset = json.loads(Path(__file__).with_name('mail_internal_fill_v1.json').read_text())
    atoms = [dict(role=f'internal_void_{index:03}', primitive='cube', export=True,
                  location=[0,0,0], dimensions=box['dimensions'], frame_mm=box['frame_mm'], bevel=0)
             for index, box in enumerate(preset['boxes'])]
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.mail-internal-fill', version=1,
        name='Sealed internal mail void fill', family='manufacturing-internal-fill',
        required_anchors=['mount'], semantic_slots=['mono'], output_roles=[a['role'] for a in atoms],
        parameters=dict(seed=seed, atoms=atoms, operations=[], landmarks={'mount':[0,0,0]},
                        source_component=preset['source_component'],
                        source_definition_sha256=preset['source_definition_sha256'],
                        design='Fill sealed microscopic pockets inside the existing exterior; original links and backing remain unchanged.'))))
