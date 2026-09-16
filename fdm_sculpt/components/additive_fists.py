"""Restore uncut fists and grow rounded tapered stock up from the cuffs."""
from copy import deepcopy
import math
from .elves_v2 import identity, point
from .spearman_overhangs import finish, ramp


def revised_parts(definitions,manifest,seed):
    if type(seed) is not int or seed!=manifest['seed']:
        raise ValueError('Use the pinned integer seed')
    result=[]
    for item in manifest['hands']:
        source=definitions[item['source']]
        if source.sha256!=item['sha256']:raise ValueError('Pinned hand changed')
        data=deepcopy(source.to_dict());p=data['parameters']
        p['atoms']=[a for a in p['atoms'] if a['role']!='fist_rising_envelope']
        p['operations']=[op for op in p['operations'] if op['operand']!='fist_rising_envelope']
        forearm=next(a for a in p['atoms'] if a['role']=='cloth_forearm')
        cuff=point(forearm['frame_mm'],[0,0,forearm['depth']/2])
        additions=[]
        for atom in p['atoms']:
            if not atom['export'] or atom['primitive'] not in ('sphere','cube'):continue
            if not any(k in atom['role'] for k in ('palm','fingers','thumb','falconry_glove')):continue
            matrix=atom.get('frame_mm',identity());center=point(matrix,atom['location'])
            terms=[matrix[2][i]*atom['dimensions'][i]/2 for i in range(3)]
            radius_z=math.sqrt(sum(t*t for t in terms)) if atom['primitive']=='sphere' else sum(abs(t) for t in terms)
            top=[*center[:2],center[2]-.15*radius_z]
            bottom=[cuff[0],cuff[1],min(cuff[2]-.65,center[2]-radius_z-.5)]
            radius=min(.58,min(atom['dimensions'])/2)
            support=ramp(atom['role']+'_additive_taper',bottom,top,min(.27,radius*.7),radius)
            support.update(export=False,bevel=.08,bevel_segments=3)
            additions.append(support)
            p['operations'].append(dict(target=atom['role'],operand=support['role'],operation='UNION',solver='EXACT'))
        p['atoms'].extend(additions)
        p.pop('fist_fit',None)
        p['additive_fist_fit']=dict(source=source.reference,source_sha256=source.sha256,
                                    seed=seed,cuff=cuff,uncut_hand_atoms=True)
        p['provenance']='Original hand primitives and grip alignment retained without fist-envelope intersections. Rounded tapered additions rise from inside the sleeve beneath the palm, fingers and thumb. Visual-only.'
        data.update(version=item['version'],name=source.name.split(' with tapered fist underside')[0]+' with uncut fist and additive underside')
        result.append(finish(data))
    return result
