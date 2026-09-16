"""Shorten only the sole toe projection while preserving the heel and boot."""
from copy import deepcopy
from .elves_v2 import point
from .spearman_overhangs import finish


def revised_parts(definitions,manifest,seed):
    if type(seed) is not int or seed!=manifest['seed']:
        raise ValueError('seed must match the pinned sole manifest')
    result=[]
    for item in manifest['sources']:
        source=definitions[item['source']]
        if source.sha256!=item['definition_sha256']:
            raise ValueError('pinned shoe source changed')
        data=deepcopy(source.to_dict()); p=data['parameters']
        sole=next(a for a in p['atoms'] if a['role'].endswith('_sole'))
        toe=next(a for a in p['atoms'] if a['role'].endswith('_toe'))
        if sole['frame_mm']!=toe['frame_mm']:
            raise ValueError('sole and toe need a shared foot frame')
        heel=sole['location'][1]+sole['dimensions'][1]/2
        front=toe['location'][1]-toe['dimensions'][1]/2-manifest['toe_projection_mm']
        old_length=sole['dimensions'][1]
        sole['dimensions'][1]=heel-front
        sole['location'][1]=(heel+front)/2
        p['landmarks'][sole['role']]=point(sole['frame_mm'],sole['location'])
        if 'shoe_fit' in p:p['shoe_fit']['sole_length_mm']=sole['dimensions'][1]
        p.update(sole_fit=dict(source=source.reference,source_sha256=source.sha256,
                              seed=seed,toe_projection_mm=manifest['toe_projection_mm'],
                              removed_front_mm=old_length-sole['dimensions'][1]),
                 provenance='Shorten the sole at the toe, leaving a small 0.04 mm front rim. Heel, toe upper, width, thickness, stance and skirt clearance cuts preserved. Visual-only.')
        data.update(version=item['version'],name=source.name+' with close-fitting sole')
        result.append(finish(data))
    return result
