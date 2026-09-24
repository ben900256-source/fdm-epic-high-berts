from copy import deepcopy
from .spearman_overhangs import finish
SOURCES=(
 'aurelian.readable-helmet-trial@2',
 'aurelian.sergeant-helmet-accepted-r6@2',
 'aurelian.swordmaster-sergeant-helmet-accepted-r2@2',
 'aurelian.dragon-prince-helmet-accepted-r6@2',
)
def revised_parts(definitions):
 out={}
 for ref in SOURCES:
  source=definitions[ref];data=deepcopy(source.to_dict());data.update(version=source.version+1,name=source.name+' - 20 percent taller shell')
  p=data['parameters'];
  for a in p['atoms']:
   role=a['role']
   if role in ('helmet_crown','nape_ellipsoid','helmet_face_opening','face_opening','nape_front_clearance','dragon_crown'):
    if 'dimensions' in a:a['dimensions'][2]*=1.20
    if 'depth' in a and role=='dragon_crown':a['depth']*=1.20
   elif role in ('helmet_tapered_tip',):
    a['depth']*=1.20
  p['taller_helmet']=dict(source=ref,source_sha256=source.sha256,height_factor=1.20,
      print_scale=1.3,seed=1001,status='visual-only')
  out[ref]=finish(data)
 return out
