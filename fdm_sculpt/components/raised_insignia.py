from copy import deepcopy
from .spearman_overhangs import finish

def revised_part(definitions):
    source=definitions['aurelian.readable-insignia-trial@4']
    data=deepcopy(source.to_dict());data.update(version=5,name='Flat seahorse relief with extended face and supporting ramps')
    p=data['parameters'];original=list(p['atoms']);ramps=[]
    for atom in original:
        atom['depth']=.56
        atom['bevel']=.03
        ramp=deepcopy(atom);ramp['role']=atom['role']+'_support_ramp';ramp['export']=False;ramp['depth']=.18;ramp['bevel']=.04
        ramp['scale']=[v*1.14 for v in atom.get('scale',[1,1,1])]
        if 'frame_mm' in ramp:ramp['frame_mm'][1][3]+=.13
        ramps.append(ramp)
    # Ramps are unioned first, then the extended relief grows out of them.
    atoms=[]
    for ramp,atom in zip(ramps,original):atoms.extend([ramp,atom])
    p['atoms']=atoms
    ops=[]
    for ramp,atom in zip(ramps,original):
        ops.append(dict(operand=ramp['role'],operation='UNION',solver='EXACT',target='seahorse_head'))
        if atom['role'] != 'seahorse_head':
            ops.append(dict(operand=atom['role'],operation='UNION',solver='EXACT',target='seahorse_head'))
    p['operations']=ops
    p['raised_insignia']=dict(source=source.reference,source_sha256=source.sha256,
        relief_depth_source=.56,ramp_depth_source=.18,ramp_scale=1.14,print_scale=1.3,
        seed=1001,status='visual-only')
    return finish(data)
