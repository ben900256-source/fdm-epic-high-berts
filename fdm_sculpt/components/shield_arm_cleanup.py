"""Remove the redundant cylinder beneath the standing guard's forearm armor."""
from copy import deepcopy

from .spearman_overhangs import finish


def revised_part(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    data = deepcopy(definitions['aurelian.left-arm@3'].to_dict())
    data.update(version=4, name='Shield arm without redundant forearm cylinder')
    params = data['parameters']
    params['atoms'] = [a for a in params['atoms'] if a['role'] != 'left_forearm']
    params['landmarks'].pop('left_forearm')
    params['cleanup'] = dict(source='aurelian.left-arm@3', seed=seed,
                             removed_role='left_forearm', feedback_id='01B6')
    params['provenance'] = 'Removed the redundant forearm cylinder; preserved the vambrace, elbow, cuff, hand and reviewed arm pose. Visual-only.'
    return finish(data)
