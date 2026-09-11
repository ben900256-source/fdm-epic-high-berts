"""Second elf proof: larger leaf shields, flared hems and five articulated poses.

Derives new parametric revisions from the explicitly pinned first proof, never
from evaluated meshes. Complete geometry and rigid frames are in each definition.
"""
from __future__ import annotations

from copy import deepcopy
import math

from .core import ComponentDefinition


def identity():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


def multiply(left, right):
    return [[sum(left[i][k]*right[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translation(vector):
    matrix = identity()
    for i, value in enumerate(vector):
        matrix[i][3] = value
    return matrix


def rotation(degrees):
    x,y,z = [math.radians(value) for value in degrees]
    cx,sx,cy,sy,cz,sz = math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx, 0],
            [sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx, 0],
            [-sy, cy*sx, cy*cx, 0], [0,0,0,1]]


def frame(pivot, angles, offset=(0,0,0)):
    return multiply(translation([p+d for p,d in zip(pivot,offset)]),
                    multiply(rotation(angles),translation([-v for v in pivot])))


def point(matrix, value):
    return [round(sum(matrix[i][j]*value[j] for j in range(3))+matrix[i][3],9) for i in range(3)]


# Angles are XYZ degrees; forward is -Y. Pose choices are fixed, never random.
POSES = {
    "a": dict(name="watching left", source="a", body=(-1,-1.5,-7), head=(0,-2,-12),
              shield=(-3,2,-8), shield_offset=(0,0,0), feet=(-0.18,0.20), knees=(-0.17,0.10),
              stance=0.68, knee_width=0.69, spear_pitch=-1.4, grip=5.35, left_grip=4.70, flare=1.32),
    "b": dict(name="braced guard", source="b", body=(2,1.5,6), head=(1,0,8),
              shield=(3,-2,12), shield_offset=(0.03,-0.10,0), feet=(0.15,-0.28), knees=(-0.36,-0.22),
              stance=0.76, knee_width=0.83, spear_pitch=1.8, grip=5.15, left_grip=4.55, flare=1.38),
    "c": dict(name="stepping forward", source="c", body=(2.4,0,-2), head=(-1,1,6),
              shield=(-4,1.5,-4), shield_offset=(0,-0.12,0), feet=(-0.43,0.34), knees=(-0.27,0.16),
              stance=0.67, knee_width=0.72, spear_pitch=0.4, grip=5.65, left_grip=4.90, flare=1.34),
    "d": dict(name="turning right", source="a", body=(-1.2,-1,8), head=(1,2,13),
              shield=(2,3,16), shield_offset=(0.02,0.03,0), feet=(0.28,-0.12), knees=(0.04,-0.22),
              stance=0.71, knee_width=0.76, spear_pitch=2.1, grip=5.80, left_grip=4.75, flare=1.36),
    "e": dict(name="settling stance", source="a", body=(0.7,1.8,-5), head=(-1,-1,-3),
              shield=(-2,-1.5,-12), shield_offset=(0.04,-0.03,0), feet=(-0.06,0.32), knees=(-0.12,0.23),
              stance=0.73, knee_width=0.74, spear_pitch=-1.9, grip=5.25, left_grip=4.60, flare=1.35),
}


def make_definitions(originals):
    definitions = []
    by_pose = {d.component_id[-1]:d for d in originals}
    for pose,settings in POSES.items():
        source = by_pose[settings["source"]]
        if source.version != 1:
            raise ValueError("elf revision 2 derives only from pinned revision 1")
        parameters = deepcopy(source.to_dict()["parameters"])
        atoms = parameters["atoms"]
        by_role = {atom["role"]:atom for atom in atoms}
        body_frame = frame((0,0,3.75),settings["body"])
        head_frame = multiply(body_frame,frame((0,0,6.75),settings["head"]))
        shield_frame = frame((-0.42,-1.05,0.0), settings["shield"],
                             (*settings["shield_offset"][:2],-0.14))
        spear_frame = frame((1.05,-0.76,0), (settings["spear_pitch"],0,0))
        cloak_frame = frame((0,0,0),(0,0,settings["body"][2]*0.55))

        for role in ("torso","cuirass_lower","cuirass_upper","collar","skirt_core",
                     "skirt_rising_underlay","skirt_lame_0","skirt_lame_1","skirt_lame_2"):
            by_role[role]["frame_mm"] = body_frame
        for role in ("cranium","chin","nose_plane","brow","helmet_crown","temple_-1","temple_1"):
            by_role[role]["frame_mm"] = head_frame
        cloak = by_role["cloak"]
        cloak.update(radius1=settings["flare"],radius2=0.92,scale=[1,0.59,1],frame_mm=cloak_frame)
        by_role["skirt_core"].update(radius1=1.30,radius2=0.97,scale=[1,0.75,1])
        by_role["torso"].update(radius1=0.93,radius2=1.04,depth=2.20,
                                location=[0,0,5.10],scale=[1,0.76,1])
        by_role["skirt_rising_underlay"].update(radius1=0.99,radius2=1.30)
        for i in range(3):
            by_role[f"skirt_lame_{i}"].update(radius1=1.30-i*0.10,radius2=1.00-i*0.075)

        # Rebuild every leg segment between articulated landmarks. Sole planes
        # remain planted while knee bend, stride and hip orientation vary.
        for index,(side,sign) in enumerate((("left",-1),("right",1))):
            y = settings["feet"][index]
            ankle = [sign*settings["stance"],y,0.72]
            knee = [sign*settings["knee_width"],settings["knees"][index],2.24+index*0.10]
            hip = point(body_frame,(sign*0.51,0,3.75))
            foot_frame = frame(ankle,(0,0,sign*(9+index*3)+settings["body"][2]*0.25))
            toe = point(foot_frame,(ankle[0],y-0.42,0.22))
            heel = point(foot_frame,(ankle[0],y+0.15,0.22))
            parameters["legs"][side] = dict(hip=hip,knee=knee,ankle=ankle,heel=heel,toe=toe,
                femur_axis=[knee[i]-hip[i] for i in range(3)],
                shin_axis=[ankle[i]-knee[i] for i in range(3)],
                foot_axis=[toe[i]-heel[i] for i in range(3)])
            by_role[side+"_sole"].update(dimensions=[0.91,1.32,0.35],
                location=[ankle[0],y-0.12,0.10],frame_mm=foot_frame)
            by_role[side+"_toe"].update(location=[ankle[0],y-0.42,0.22],frame_mm=foot_frame)
            by_role[side+"_ankle"]["location"] = ankle
            by_role[side+"_knee"]["location"] = knee
            by_role[side+"_hip"]["location"] = hip
            by_role[side+"_shin"].update(start=ankle,end=knee)
            by_role[side+"_thigh"].update(start=knee,end=hip)

        # Leaf lens: 2.10 mm wide and 6.17 mm tall versus 1.30 x 4.74 mm.
        for role,x in (("shield",-4.42),("shield_lens_mask",3.58)):
            by_role[role].update(radius=5.05,depth=0.92,location=[x,-1.05,3.15],frame_mm=shield_frame)
        by_role["shield_ground_heel"].update(radius1=0.59,radius2=0.38,
            location=[-0.42,-1.05,0.50],frame_mm=shield_frame)
        by_role["shield_spine"].update(dimensions=[0.32,0.35,5.30],
            location=[-0.42,-1.61,3.07],frame_mm=shield_frame)
        for role in ("spear","spear_leaf_lower","spear_leaf_tip"):
            atom = by_role[role]
            for key in ("location","start","end"):
                if key in atom:
                    atom[key][0] = 1.05
            atom["frame_mm"] = spear_frame
        by_role["shield_spear_brace"].update(
            start=point(shield_frame,(-0.25,-1.05,3.10)),
            end=point(spear_frame,(1.05,-0.76,4.50)))

        arms = {}
        for side,sign in (("left",-1),("right",1)):
            old_grip = [-0.72,-0.66,4.9] if side=="left" else [1.15,-0.72,5.4]
            new_grip = [-0.60,-0.58,settings["left_grip"]] if side=="left" else [1.00,-0.72,settings["grip"]]
            equipment_frame = shield_frame if side=="left" else spear_frame
            hand_frame = multiply(equipment_frame,translation([b-a for a,b in zip(old_grip,new_grip)]))
            shoulder = point(body_frame,(sign*0.86,0,5.98))
            elbow = point(body_frame,(-1.05,-0.25,4.93) if side=="left" else (1.0,0.05,settings["grip"]-0.34))
            grip = point(equipment_frame,new_grip)
            arms[side] = dict(shoulder=shoulder,elbow=elbow,grip=grip)
            by_role[side+"_sleeve_root"].update(start=point(body_frame,(sign*0.70,0.24,3.95)),end=elbow)
            by_role[side+"_upper_arm"].update(start=shoulder,end=elbow)
            by_role[side+"_forearm"].update(start=elbow,end=grip)
            by_role[side+"_elbow"]["location"] = elbow
            by_role[side+"_pauldron"].update(location=[sign*0.86,0,5.98],frame_mm=body_frame)
            for suffix in ("palm","grouped_fingers","thumb","cuff"):
                by_role[side+"_"+suffix]["frame_mm"] = hand_frame

        parameters.update(adapter_version=2,pose_name=settings["name"],pose_settings=settings,
                          source_reference=source.reference,source_definition_sha256=source.sha256,
                          arms=arms,shield_width_mm=2.10,shield_height_mm=round(2*math.sqrt(5.05**2-4**2),9),
                          cloak_hem_width_mm=2*settings["flare"],
                          frames=dict(body=body_frame,head=head_frame,shield=shield_frame,spear=spear_frame),
                          status="revision-2-visual-review-candidate")
        definitions.append(ComponentDefinition(component_id=f"aurelian.spearman.{pose}",version=2,
            name="Aurelian leafguard — "+settings["name"],family="elf-proof",
            required_anchors=("sole",),semantic_slots=("mono",),output_roles=source.output_roles,
            parameters=parameters))
    return tuple(definitions)
