from copy import deepcopy
from .spearman_overhangs import finish

def revised_part(definitions):
 source=definitions['aurelian.readable-insignia-trial@5'];data=deepcopy(source.to_dict())
 data.update(version=6,name='Fiercer flat seahorse with pointed snout and brow')
 p=data['parameters'];atoms={a['role']:a for a in p['atoms']}
 atoms['seahorse_head']['scale'][0]*=1.08;atoms['seahorse_head']['scale'][1]*=1.08
 atoms['seahorse_snout']['scale'][0]*=.78;atoms['seahorse_snout']['scale'][1]*=1.18
 atoms['seahorse_crest']['scale'][0]*=1.12;atoms['seahorse_crest']['scale'][1]*=1.12
 # A short attached brow gives the profile a sharper, more predatory break.
 brow=deepcopy(atoms['seahorse_crest']);brow['role']='seahorse_brow';brow['export']=False;brow['depth']=.56
 brow['scale']=[.16,.34,1];brow['frame_mm'][0][3]+=.12;brow['frame_mm'][1][3]-=.04
 p['atoms'].append(brow);p['operations'].append(dict(operand='seahorse_brow',operation='UNION',solver='EXACT',target='seahorse_head'))
 p['fierce_seahorse']=dict(source=source.reference,source_sha256=source.sha256,
   head_scale=1.08,snout_width=.78,snout_length=1.18,brow='attached angular brow',
   print_scale=1.3,seed=1001,status='visual-only')
 return finish(data)
