"""Seat cloth sleeves along the posed upper arms without changing geometry."""
from copy import deepcopy
import math

from .elves_v2 import multiply, point

DROP_MM=.25


def normalize(v):
    length=math.sqrt(sum(x*x for x in v))
    return [x/length for x in v]


def align_left_sleeves(assembly, definitions):
    result=deepcopy(assembly)
    placements={p['instance_id']:p for p in result['placements']}
    for name,sleeve in placements.items():
        if not name.endswith('/left-tunic'):
            continue
        arm=placements[name.replace('/left-tunic','/left-arm')]
        atom=next(a for a in definitions[arm['part']].to_dict()['parameters']['atoms'] if a['role']=='left_upper_arm')
        frame=multiply(arm['mount'],atom['frame_mm'])
        shoulder,elbow=point(frame,atom['start']),point(frame,atom['end'])
        z=normalize([b-a for a,b in zip(shoulder,elbow)])
        # Preserve the sleeve's lateral roll while aligning its long axis.
        x=[sleeve['mount'][i][0] for i in range(3)]
        projection=sum(a*b for a,b in zip(x,z))
        x=normalize([a-projection*b for a,b in zip(x,z)])
        y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
        origin=[a+DROP_MM*b for a,b in zip(shoulder,z)]
        sleeve['mount']=[[round(x[i],9),round(y[i],9),round(z[i],9),round(origin[i],9)] for i in range(3)]+[[0,0,0,1]]
    return result
