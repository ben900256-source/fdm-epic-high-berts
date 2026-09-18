"""Full separate spears seated in open palm channels, with no adapter collars."""
from copy import deepcopy
from math import pi, atan2, cos, sin, sqrt

from .core import ComponentDefinition
from .elves_v2 import identity, multiply
from .parts import inverse_rigid, validate_part
from .spear_kit import cube, definition, operation

BOTTOM_Z = -4.85
TIP_Z = 8.75
BED_AXIS_Z = .3
CHANNEL_HALF_WIDTH = .6
CLEARANCE = .10
RECESS_DEPTH = .65
BACKING_STOCK = .75
FINGER_ROOT = .50
CHANNEL_BACK = -.3-CLEARANCE
CHANNEL_LIP = CHANNEL_BACK+RECESS_DEPTH
INSERTION_TRAVEL = 15.0


def point(frame, xyz):
    return [sum(frame[i][j]*xyz[j] for j in range(3))+frame[i][3] for i in range(3)]


def clearance_profile():
    """Swept envelopes in grip coordinates: X opens forward, Z follows shaft.

    The full spear translates along +X from its seat to free space. A separate
    wider head envelope includes both tapered head primitives and their ends.
    """
    return ((CHANNEL_BACK, INSERTION_TRAVEL+.6, CHANNEL_HALF_WIDTH, BOTTOM_Z-.1, 7.05+.1),
            (CHANNEL_BACK, INSERTION_TRAVEL+.84, 1.02, 6.65-.1, TIP_Z+.1))


def clearance_atoms(frame, prefix='insertion'):
    result=[]
    for i,(back,front,half,z0,z1) in enumerate(clearance_profile()):
        atom=cube(f'{prefix}_{i}', (front-back,2*half,z1-z0),
                  ((front+back)/2,0,(z0+z1)/2))
        atom['frame_mm']=frame
        result.append(atom)
    return result


def cone(role, start, end, r1, r2, *, export=False, horizontal=False, z_scale=1):
    atom=dict(role=role,primitive='cone',radius1=r1,radius2=r2,depth=end-start,
              vertices=48,export=export,bevel=0,location=[0,.46,(start+end)/2])
    if horizontal:
        atom.update(location=[0,(start+end)/2,BED_AXIS_Z],rotation=[-pi/2,0,0],scale=[1,z_scale,1])
    return atom


def placement(part, name, mount):
    return dict(instance_id=name,part=part.reference,definition_sha256=part.sha256,mount=mount)


def full_spear():
    atoms = [cone('shaft', 0, 7.05-BOTTOM_Z, .5, .5, export=True, horizontal=True),
             cone('head_root', 6.65-BOTTOM_Z, 7.60-BOTTOM_Z, .45, .9, export=True, horizontal=True, z_scale=.8),
             cone('head_tip', 7.50-BOTTOM_Z, TIP_Z-BOTTOM_Z, .92, .40, export=True, horizontal=True, z_scale=.8),
             cube('bed_cut', (10, 40, 10), (0, 10, -5))]
    part = definition('full-rounded-grip-spear-trial', 'Full rounded spear, flat only underneath', atoms,
                      [operation(a['role'], 'bed_cut', 'DIFFERENCE') for a in atoms[:-1]],
                      shaft_diameter_mm=1, shaft_height_mm=.8, shaft_bed_width_mm=.8,
                      length_mm=TIP_Z-BOTTOM_Z, attachment='Open palm channel and glue; no pin or collar')
    data=part.to_dict()
    data['version']=2
    return validate_part(ComponentDefinition.from_dict(data))


def frame():
    atoms = [cube('frame', (17.6, .8, .8), (8, -.8, .4), export=True)]
    ops = []
    def add(a):
        atoms.append(a)
        ops.append(operation('frame', a['role']))
    for i in range(5):
        add(cube(f'butt_gate_{i}', (.45,.65,.4), (i*4,-.125,.2)))
    part=definition('full-rounded-grip-spear-frame-trial', 'Five full spears joined only at their butts',
                    atoms, ops, gate_width_mm=.45, gate_height_mm=.4, insert_count=5,
                    attachment='Single crossbar with five butt gates; no surrounding rails or side tabs')
    data=part.to_dict()
    data['version']=2
    return validate_part(ComponentDefinition.from_dict(data))


def grip(source, arm_to_spear, pose, center_z, arm_mount):
    data = source.to_dict()
    data.update(component_id=f'aurelian.open-spear-grip-{pose}-trial', version=10 if pose in ('2','4') else 9,
                name=f'Centered curled spear grip, {pose}', family='right-arm')
    params = data['parameters']
    # Keep every sleeve primitive and operation. Replace only the hand; the
    # original cuff is the attachment landmark, never an adjusted placement.
    sleeve_ops=[o for o in params['operations'] if o['target']=='robe_sleeve']
    sleeve_roles={'robe_sleeve'} | {o['operand'] for o in sleeve_ops}
    params['atoms']=[a for a in params['atoms'] if a['role'] in sleeve_roles]
    params['operations']=list(sleeve_ops)
    # Cross the cutter's floor by .06 mm before the difference. A coincident
    # palm face can make Exact retain a cutter sheet in some rotated poses.
    palm=cube('right_palm', (BACKING_STOCK+.06,2.2,1.42),
              (CHANNEL_BACK-BACKING_STOCK/2+.03,0,center_z), export=True, bevel=.25)
    palm['frame_mm']=arm_to_spear
    params['atoms'].append(palm)
    def add(atom):
        atom['frame_mm']=arm_to_spear
        params['atoms'].append(atom)
        params['operations'].append(operation('right_palm',atom['role']))
    for i in range(4):
        add(dict(role=f'curled_finger_{i}',primitive='sphere',dimensions=[1.4,.70,.46],
                 location=[CHANNEL_LIP-.7,.78,center_z-.45+i*.30],
                 segments=32,ring_count=20,export=False))
    add(dict(role='curled_thumb',primitive='sphere',dimensions=[1.4,.74,1.25],
             location=[CHANNEL_LIP-.7,-.8,center_z+.10],segments=32,ring_count=20,export=False))
    # Continuous finger stock carries the shallow knuckle relief. The former
    # separate rounded lobes left an overhanging underside at every finger.
    add(cube('finger_stock',(1.28,.56,1.34),(-.45,.78,center_z),bevel=.14))
    add(cube('thumb_stock',(1.28,.60,1.13),(-.45,-.8,center_z+.10),bevel=.14))
    cuff=point(inverse_rigid(arm_to_spear),params['landmarks']['right_cuff'])
    # A rounded palm heel joins the unchanged cuff to the backing of the seat.
    heel=[CHANNEL_BACK-.35,0,center_z-.18]
    add(dict(role='palm_heel',primitive='between',start=cuff,end=heel,
             radius=.43,export=False))
    # Clip closed hand primitives before joining them: this avoids Exact
    # artifacts at the overlapping palm/finger seam in rotated poses.
    hand_unions=params['operations'][len(sleeve_ops):]
    params['operations']=list(sleeve_ops)
    targets=['right_palm']+[o['operand'] for o in hand_unions]
    wrist=point(arm_mount,params['landmarks']['right_cuff'])
    apex_drop={'2':.62,'4':.85}.get(pose,.6)
    for axis in range(2):
        for sign in (-1,1):
            # Upward-opening square taper rooted inside the original cuff.
            # Each cut plane is 45 degrees in WORLD printing orientation.
            n=[0,0,1/sqrt(2)]; n[axis]=-sign/sqrt(2)
            tangent=[0,0,sign/sqrt(2)]; tangent[axis]=1/sqrt(2)
            across=[n[1]*tangent[2]-n[2]*tangent[1],
                    n[2]*tangent[0]-n[0]*tangent[2],
                    n[0]*tangent[1]-n[1]*tangent[0]]
            origin=[wrist[0],wrist[1],wrist[2]-apex_drop]
            world=[[tangent[i],across[i],n[i],origin[i]] for i in range(3)]+[[0,0,0,1]]
            cutter=cube(f'wrist_underside_{axis}_{sign}',(20,20,20),(0,0,-10))
            cutter['frame_mm']=multiply(inverse_rigid(arm_mount),world)
            params['atoms'].append(cutter)
            for role in targets:
                params['operations'].append(operation(role,cutter['role'],'DIFFERENCE'))
    for cutter in clearance_atoms(arm_to_spear):
        params['atoms'].append(cutter)
        for role in ['robe_sleeve']+targets:
            params['operations'].append(operation(role,cutter['role'],'DIFFERENCE'))
    params['operations'].extend(hand_unions)
    data['output_roles']=['robe_sleeve','right_palm']
    params.pop('additive_fist_fit',None)
    params['landmarks']['grip_center']=params['landmarks']['right_grouped_fingers']
    params['open_grip_trial'] = dict(source=source.reference, source_sha256=source.sha256,
        channel_width_mm=2*CHANNEL_HALF_WIDTH, flat_back_clearance_mm=.1,
        recess_depth_mm=RECESS_DEPTH, backing_stock_mm=BACKING_STOCK,
        finger_root_mm=FINGER_ROOT, grip_frame_mm=arm_to_spear, center_z_mm=center_z,
        insertion_travel_mm=INSERTION_TRAVEL,
        underside=dict(slope_degrees_from_vertical=45,apex_below_cuff_mm=apex_drop,
                       full_depth_at_center_z_offset_mm=.45,relief='Shallow connected finger stock'),
        attachment='Front-opening centered seat for lateral insertion and glue; visual-only')
    params['provenance'] = 'Original sleeve and cuff preserved; centered primitive curled hand with owned Exact insertion clearance. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))


def cleared_part(source, instance_id, cuts):
    data=source.to_dict()
    data.update(component_id='aurelian.centered-grip-clearance-'+instance_id.replace('/','-')+'-trial',
                version=1,name=source.name+'; centered spear insertion clearance')
    p=data['parameters']
    records=[]
    for pose,frame,roles in cuts:
        for atom in clearance_atoms(frame,f'spear_{pose}_insertion'):
            p['atoms'].append(atom)
            for role in roles:
                p['operations'].append(operation(role,atom['role'],'DIFFERENCE'))
        records.append(dict(pose=pose,frame_mm=frame,roles=roles))
    p['centered_grip_clearance']=dict(source=source.reference,source_sha256=source.sha256,cuts=records)
    if instance_id=='row-04/skirt':
        # The evaluated swept cut leaves a 0.0014 mm-high detached tip of this
        # mail link. A local primitive removes only that chip; its Z interval
        # is separated from the connected remainder by more than 0.015 mm.
        data['version']=2
        chip=cube('cut_off_mail_tip',(.02,.02,.02),(1.59,-.19,-4.03))
        p['atoms'].append(chip)
        p['operations'].append(operation('skirt_link_2_29',chip['role'],'DIFFERENCE'))
        p['centered_grip_clearance']['cleanup']='Local Exact box removes the detached cut-off tip of skirt_link_2_29.'
    p['provenance']='Reviewed neighboring part with local Exact swept-spear clearance; visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))


def assemblies(source, catalog, clearance_targets):
    row = deepcopy(source)
    parts = [full_spear(), frame()]
    by_id = {p['instance_id']:p for p in row['placements']}
    spears = []
    grip_frames = {}
    for i in range(1,6):
        prefix=f'row-{i:02}'
        old_spear=by_id[prefix+'/spear']
        arm=by_id[prefix+'/right-arm']
        source_arm=catalog[arm['part']]
        if i==5:
            # Retain the shoulder rotation already used by the reviewed trial.
            shoulder=next(a for a in source_arm.to_dict()['parameters']['atoms'] if a['role']=='cloth_shoulder')
            shoulder_frame=multiply(arm['mount'],shoulder['frame_mm'])
            pivot=[shoulder_frame[k][3] for k in range(3)]
            angle=-atan2(old_spear['mount'][0][2],old_spear['mount'][2][2])
            c,s=cos(angle),sin(angle)
            around=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
            for k in range(3):
                around[k][3]=pivot[k]-sum(around[k][j]*pivot[j] for j in range(3))
            arm['mount']=multiply(around,arm['mount'])
            old_spear['mount']=multiply(around,old_spear['mount'])
        original_center=point(arm['mount'],source_arm.to_dict()['parameters']['landmarks']['right_grouped_fingers'])
        center=point(inverse_rigid(old_spear['mount']),original_center)
        # Roll the flat back toward the palm; keep the shaft direction and Z
        # extent. Translation is perpendicular to the existing shaft axis.
        to_grip=[[0,1,0,center[0]],[-1,0,0,center[1]],[0,0,1,0],[0,0,0,1]]
        grip_frame=multiply(old_spear['mount'],to_grip)
        grip_frames[str(i)]=grip_frame
        owned_frame=multiply(inverse_rigid(arm['mount']),grip_frame)
        hand=grip(source_arm, owned_frame, str(i),center[2],arm['mount'])
        parts.append(hand)
        arm.update(part=hand.reference, definition_sha256=hand.sha256)
        print_to_local=[[0,0,1,-BED_AXIS_Z],[1,0,0,0],
                        [0,1,0,BOTTOM_Z],[0,0,0,1]]
        spears.append(placement(parts[0], prefix+'/separate-spear', multiply(grip_frame,print_to_local)))
    row['placements']=[p for p in row['placements'] if not p['instance_id'].endswith(('/spear','/spear-insert'))]
    # Retain the reviewed placement-only stagger and the strip footprint.
    stagger={'row-01':.25,'row-02':-.4,'row-05':-.45}
    for p in row['placements']+spears:
        p['mount'][1][3]+=stagger.get(p['instance_id'].split('/')[0],0)
    for pose,f in grip_frames.items():
        f[1][3]+=stagger.get(f'row-{int(pose):02}',0)
    for p in row['placements']:
        targets=clearance_targets.get(p['instance_id'],[])
        if not targets:
            continue
        src=catalog[p['part']]
        cuts=[]
        for target in targets:
            if target['source']!=src.reference or target['source_sha256']!=src.sha256:
                raise ValueError('stale clearance target: '+p['instance_id'])
            cuts.append((target['pose'],multiply(inverse_rigid(p['mount']),grip_frames[target['pose']]),target['roles']))
        cleared=cleared_part(src,p['instance_id'],cuts)
        parts.append(cleared)
        p.update(part=cleared.reference,definition_sha256=cleared.sha256)
    row.update(assembly_id='open-grip-spear-row-trial', label='Open grip trial - empty hands, no adapters')
    assembled=deepcopy(row)
    assembled.update(assembly_id='open-grip-spear-assembled-trial', label='Open grip trial - full separate spears assembled')
    assembled['placements'].extend(spears)
    kit=dict(schema_version=1,assembly_id='full-rounded-spear-kit-trial',
        label='Full rounded spears - flat-backed, joined only at the butts',
        placements=[placement(parts[1],'kit/frame',identity())])
    for i in range(5):
        mount=identity()
        mount[0][3]=4*i
        kit['placements'].append(placement(parts[0],f'kit/spear-{i+1}',mount))
    return parts, (row,kit,assembled)
