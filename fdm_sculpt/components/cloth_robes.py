"""Soft robe folds and close-fitting cloth sleeves built from local Exact CSG."""
from copy import deepcopy
import math

from .spearman_overhangs import finish, ramp
from .elves_v2 import multiply


def ellipsoid(role, start, end, width, depth):
    axis = ramp(role, start, end, 1, 1)
    length = axis['depth']
    return dict(role=role, primitive='sphere', export=False, location=[0, 0, 0],
                dimensions=[width, depth, length], frame_mm=axis['frame_mm'],
                segments=24, ring_count=20)


def operation(target, operand, kind='UNION'):
    return dict(target=target, operand=operand, operation=kind, solver='EXACT')


def skirt_folds(params, target, *, bottom, top, lower, upper, scale, count):
    """Broad gathered ridges with tapered valleys following the garment flare."""
    for i in range(count):
        angle = 2*math.pi*(i+.35)/count
        lo = bottom+.08+(i%3)*.055
        hi = top-.13-(i%2)*.09
        radius = lambda z: lower+(upper-lower)*(z-bottom)/(top-bottom)
        def point(z, a, offset=0):
            r=radius(z)+offset
            return [r*math.cos(a), r*scale*math.sin(a), z]
        # The swell blends into the body at each end rather than leaving a rod.
        fold = ellipsoid(f'robe_fold_{i}', point(lo, angle, -.04),
                         point(hi, angle+.055, -.06), .46, .46)
        params['atoms'].append(fold)
        params['operations'].append(operation(target, fold['role']))
        valley = ramp(f'robe_valley_{i}', point(lo+.07, angle+math.pi/count, .055),
                      point(hi-.12, angle+math.pi/count+.04, .035), .18, .075)
        valley['export'] = False
        params['atoms'].append(valley)
        params['operations'].append(operation(target, valley['role'], 'DIFFERENCE'))


def sleeve(definitions, side, seed):
    source = f'aurelian.{side}-tunic@'+('2' if side=='left' else '3')
    data = deepcopy(definitions[source].to_dict())
    data.update(version=4, name=side.title()+' softly folded robe sleeve')
    root = side+'_robe_sleeve'
    params = dict(atoms=[dict(role=root, primitive='sphere', export=True,
                             location=[0,0,.15], dimensions=[.82,.88,1.48],
                             segments=32, ring_count=24)], operations=[],
                  landmarks=dict(mount=[0,0,0], **{side+'_shoulder':[0,0,-.03]}),
                  seed=seed, robe_source=source,
                  provenance='Soft close-fitting shoulder emerging from the plate armhole; no pauldron cap or raised hem band. Visual-only.')
    for i, x in enumerate((-.23, .04, .25)):
        crease = ellipsoid(f'{side}_sleeve_crease_{i}', [x*.4,-.40,-.29],
                           [x,-.41,.65], .13, .18)
        params['atoms'].append(crease)
        params['operations'].append(operation(root, crease['role'], 'DIFFERENCE'))
    # A low diagonal gather reads as cloth tension at the underarm.
    gather = ellipsoid(side+'_sleeve_gather', [-.25,-.30,.37], [.23,-.32,.57], .20,.20)
    params['atoms'].append(gather)
    params['operations'].append(operation(root, gather['role']))
    data['parameters'] = params
    return finish(data)


def archer_robe(definitions, seed):
    data = deepcopy(definitions['aurelian.archer-tunic@4'].to_dict())
    data.update(version=5, name='Archer robe with gathered cloth and flowing folds')
    p=data['parameters']
    p['atoms']=[a for a in p['atoms'] if not a['role'].startswith('cloth_crease_')]
    p['operations']=[o for o in p['operations'] if not o['operand'].startswith('cloth_crease_')]
    skirt_folds(p,'tunic_body', bottom=-3.5,top=-.65,lower=1.77,upper=.96,scale=.72,count=12)
    # Diagonal chest gathers converge at the belt; retain the collar and buckle.
    for side in (-1,1):
        for i in range(2):
            fold=ellipsoid(f'chest_gather_{side}_{i}',[side*(.57+i*.12),-.44,.62-i*.18],
                           [side*(.16+i*.16),-.55,-.40],.22,.22)
            p['atoms'].append(fold)
            p['operations'].append(operation('tunic_body',fold['role']))
    p['robe_source']='aurelian.archer-tunic@4'
    p['seed']=seed
    p['provenance']='Original robe and belt retained; broad gathered folds replace thin incised lines. Visual-only.'
    return finish(data)


def spearman_robe(definitions, seed):
    data=deepcopy(definitions['aurelian.skirt@8'].to_dict())
    data.update(version=9,name='Spearman folded cloth robe beneath the breastplate')
    p=data['parameters']
    p['atoms']=[a for a in p['atoms'] if a['role'] in ('mail_skirt_backing','hem_ground_transition')]
    body=next(a for a in p['atoms'] if a['role']=='mail_skirt_backing')
    body['role']='robe_body'
    p['operations']=[]
    p.pop('chainmail',None)
    skirt_folds(p,'robe_body',bottom=-4.85,top=-.55,lower=1.55,upper=.97,scale=.75,count=14)
    p['robe_source']='aurelian.skirt@8'
    p['seed']=seed
    p['provenance']='Cloth folds replace chainmail links; original hem, foot clearance and waist mounts retained. Visual-only.'
    return finish(data)


def revised_parts(definitions, seed, *, cloth_skirt=True):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result=[sleeve(definitions,side,seed) for side in ('left','right')]
    result.append(archer_robe(definitions,seed))
    if cloth_skirt:
        result.append(spearman_robe(definitions,seed))
    return result


def fitted_sleeves(definitions, seed):
    """Second visual pass: a tapered sleeve instead of an elongated oval cap."""
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result=[]
    for side in ('left','right'):
        source=f'aurelian.{side}-tunic@4'
        data=deepcopy(definitions[source].to_dict())
        data.update(version=5,name=side.title()+' robe sleeve emerging through the armhole')
        p=data['parameters']
        root=side+'_robe_sleeve'
        # Local Z points down the arm. The small upper end nests in the hole.
        p['atoms']=[dict(role=root,primitive='cone',export=True,location=[0,0,.29],
                         depth=1.16,radius1=.28,radius2=.43,scale=[1,1.05,1],
                         vertices=48,bevel=.10,bevel_segments=4)]
        p['operations']=[]
        shoulder=dict(role=side+'_cloth_shoulder',primitive='sphere',export=False,
                      location=[0,0,-.04],dimensions=[.65,.72,.77],segments=32,ring_count=24)
        p['atoms'].append(shoulder)
        p['operations'].append(operation(root,shoulder['role']))
        for i,x in enumerate((-.19,.06,.23)):
            crease=ellipsoid(f'{side}_sleeve_crease_{i}',[x*.35,-.29,-.08],
                             [x,-.43,.81],.12,.15)
            p['atoms'].append(crease)
            p['operations'].append(operation(root,crease['role'],'DIFFERENCE'))
        p['robe_source']=source
        p['seed']=seed
        p['provenance']='Tapered cloth sleeve with a small soft shoulder seated within the armhole. No cap, metal rim or separate pauldron. Visual-only.'
        result.append(finish(data))
    return result


def folded_capes(definitions, seed):
    """Add back folds while preserving the grounded hem and front trim contact."""
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result=[]
    for suffix in ('','-b','-c','-d','-e'):
        source=f'aurelian.cape{suffix}@4'
        data=deepcopy(definitions[source].to_dict())
        data.update(version=5,name='Grounded cloth cape with hanging folds')
        p=data['parameters']
        cloak=next(a for a in p['atoms'] if a['role']=='cloak')
        phase=cloak['rotation'][2]
        def point(z,angle,offset):
            r=cloak['radius1']+(cloak['radius2']-cloak['radius1'])*z/cloak['depth']+offset
            x,y=r*math.cos(angle),r*.59*math.sin(angle)
            return [x*math.cos(phase)-y*math.sin(phase),
                    .63+x*math.sin(phase)+y*math.cos(phase),z]
        for i,degrees in enumerate((28,52,76,100,124,148)):
            angle=math.radians(degrees)
            fold=ellipsoid(f'cape_hanging_fold_{i}',point(.28+i%2*.07,angle,-.06),
                           point(5.95-i%3*.13,angle+.035,-.06),.46,.46)
            fold['frame_mm']=multiply(cloak['frame_mm'],fold['frame_mm'])
            p['atoms'].append(fold)
            p['operations'].append(operation('cloak',fold['role']))
            crease=ellipsoid(f'cape_fold_valley_{i}',point(.45,angle+.15,.045),
                             point(5.6,angle+.17,.03),.23,.23)
            crease['frame_mm']=multiply(cloak['frame_mm'],crease['frame_mm'])
            p['atoms'].append(crease)
            p['operations'].append(operation('cloak',crease['role'],'DIFFERENCE'))
        p['robe_source']=source
        p['seed']=seed
        p['provenance']='Six softly rounded hanging back folds with recessed valleys; front cape contact and ground-reaching hem preserved. Visual-only.'
        result.append(finish(data))
    return result


def front_folded_sleeves(definitions, seed):
    """Keep the folds readable on both sides of the posed sleeve frames."""
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result=[]
    for side in ('left','right'):
        source=f'aurelian.{side}-tunic@5'
        data=deepcopy(definitions[source].to_dict())
        data['version']=6
        p=data['parameters']
        for i,x in enumerate((-.19,.06,.23)):
            crease=ellipsoid(f'{side}_sleeve_front_crease_{i}',[x*.35,.29,-.08],
                             [x,.43,.81],.14,.18)
            p['atoms'].append(crease)
            p['operations'].append(operation(side+'_robe_sleeve',crease['role'],'DIFFERENCE'))
        p['robe_source']=source
        p['seed']=seed
        p['provenance']='Fitted cloth sleeve with shallow gathers on both front and back of the posed arm. Visual-only.'
        result.append(finish(data))
    return result
