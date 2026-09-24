from copy import deepcopy
from .spearman_overhangs import finish

def revised_part(definitions):
    source=definitions['aurelian.crest@4']
    data=deepcopy(source.to_dict());data.update(version=5,name='Larger crest with slightly proud front projection')
    p=data['parameters']
    for a in p['atoms']:
        role=a['role']
        if role.endswith('_front') or role=='crest_lower_taper':
            continue
        if 'dimensions' in a:
            a['dimensions'][0]*=1.12;a['dimensions'][1]*=1.08;a['dimensions'][2]*=1.08
        if 'scale' in a:
            a['scale'][0]*=1.12;a['scale'][1]*=1.08
        if 'location' in a:
            a['location'][1]-=.10
        if 'frame_mm' in a:
            a['frame_mm'][1][3]-=.10
    for key in ('crest_center','stripe_center'):
        p['landmarks'][key][1]-=.10
    p['crest_update']=dict(source=source.reference,source_sha256=source.sha256,
        width_factor=1.12,depth_factor=1.08,height_factor=1.08,front_projection_mm=.10,
        print_scale=1.3,seed=1001,status='visual-only')
    return finish(data)
