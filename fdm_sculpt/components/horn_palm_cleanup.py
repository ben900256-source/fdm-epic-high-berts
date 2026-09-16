"""Remove the redundant bulb from the horn grip, retaining its connected fingers."""
from copy import deepcopy

from .spearman_overhangs import finish


def revised_arm(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    source = definitions['aurelian.horn-arm@10']
    data = deepcopy(source.to_dict())
    p = data['parameters']
    p['atoms'] = [a for a in p['atoms'] if a['role'] != 'left_palm']
    p['landmarks'].pop('left_palm')
    p.update(seed=seed, palm_cleanup_source=source.reference,
             palm_cleanup_source_sha256=source.sha256,
             provenance='Remove the oversized palm sphere. Existing thumb connects the sleeve and grouped fingers; horn contact retained. Sleeve, elbow texture, fingers, thumb and pose unchanged. Visual-only.')
    data.update(version=11, name='Cloth horn arm without redundant palm bulb')
    return finish(data)
