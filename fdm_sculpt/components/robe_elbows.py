"""Shallow gathered cloth texture on the existing round sleeve elbows."""
from copy import deepcopy
import math

from .cloth_robes import ellipsoid, operation
from .robe_arms import add, scale, unit
from .spearman_overhangs import finish, ramp


def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def textured_elbow(source, version, seed):
    if type(seed) is not int or type(version) is not int or version<=source.version:
        raise ValueError('explicit integer seed and a new revision required')
    data=deepcopy(source.to_dict())
    p=data['parameters']
    sphere=next(a for a in p['atoms'] if a['role']=='cloth_elbow')
    shoulder,elbow,wrist=(p['cloth_pose'][k] for k in ('shoulder','elbow','wrist'))
    to_shoulder=unit([s-e for s,e in zip(shoulder,elbow)])
    to_wrist=unit([w-e for w,e in zip(wrist,elbow)])
    outer=unit(scale(add(to_shoulder,to_wrist),-1))
    across=unit(cross(to_shoulder,to_wrist))
    along=unit(cross(across,outer))

    def surface(angle,latitude,inset=0):
        direction=add(scale(along,math.sin(latitude)),
            scale(add(scale(outer,math.cos(angle)),scale(across,math.sin(angle))),math.cos(latitude)))
        return [sphere['location'][i]+direction[i]*(sphere['dimensions'][i]/2+inset) for i in range(3)]

    # Three short curved compression creases cross the outer elbow. Tapered
    # ends fade into the surface and the slight diagonal avoids a metal-band look.
    for row,latitude in enumerate((-.43,-.03,.37)):
        samples=8
        angles=[-.98+i*1.96/samples for i in range(samples+1)]
        points=[surface(a,latitude+.14*a,.012) for a in angles]
        for i,(start,end) in enumerate(zip(points,points[1:])):
            radius=lambda t:.018+.066*math.sin(math.pi*t)**.65
            atom=ramp(f'elbow_cloth_crease_{row}_{i}',start,end,
                      radius(i/samples),radius((i+1)/samples))
            atom['export']=False
            p['atoms'].append(atom)
            p['operations'].append(operation('robe_sleeve',atom['role'],'DIFFERENCE'))
    # Low, broad swells between creases tie into the sleeve's existing folds.
    # Both ends lie inside the original elbow; no hanging fabric is introduced.
    for i,latitude in enumerate((-.23,.18)):
        atom=ellipsoid(f'elbow_cloth_gather_{i}',surface(-.51,latitude-.07,-.025),
                       surface(.51,latitude+.07,-.025),.27,.27)
        p['atoms'].append(atom)
        p['operations'].append(operation('robe_sleeve',atom['role']))
    p.update(elbow_texture_source=source.reference,elbow_texture_source_sha256=source.sha256,seed=seed)
    p['provenance']='Existing sleeve and elbow sphere retained. Three shallow curved cloth creases and two low gathers texture the elbow; hands, shoulder fit and pose unchanged. Visual-only.'
    data.update(version=version,name=source.name+' with gathered elbow cloth')
    return finish(data)


def revised_parts(definitions,manifest,seed):
    if type(seed) is not int or seed!=manifest['seed']:
        raise ValueError('seed must match the pinned elbow manifest')
    result=[]
    for item in manifest['sources']:
        source=definitions[item['source']]
        if source.sha256!=item['definition_sha256']:
            raise ValueError('pinned source sleeve changed')
        result.append(textured_elbow(source,item['version'],seed))
    return result
