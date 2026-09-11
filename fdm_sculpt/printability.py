"""Conservative, profile-bound support screening of deposited FDM toolpaths.

This is a digital design screen, not a physical durability or cooling model.
It inspects previous-layer plastic, not merely the intended mesh envelope.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


@dataclass(frozen=True)
class PrintabilityCriteria:
    resolution_mm: float = 0.025
    nozzle_mm: float = 0.25
    nominal_layer_mm: float = 0.05
    first_layer_mm: float = 0.14
    # Sampling uncertainty is one raster cell. Centerline support corresponds
    # approximately to at least half a bead resting on the prior extrusion.
    raster_tolerance_mm: float = 0.025
    maximum_local_unanchored_run_mm: float = 0.25
    maximum_external_bridge_mm: float = 1.0
    maximum_internal_bridge_mm: float = 5.0
    maximum_bridge_curvature_ratio: float = 1.10
    target_overhang_degrees_from_vertical: float = 45.0
    removable_support_target: int = 0


CRITERIA = PrintabilityCriteria()
SIZE = (880,280)


def pixel(point, criteria=CRITERIA):
    return (round((point[0]+11)/criteria.resolution_mm),round((3.5-point[1])/criteria.resolution_mm))


def model_paths(layer):
    return [p for p in layer['paths'] if p[5] not in {'Skirt/Brim','Skirt','Brim'}]


def deposition_mask(paths, criteria=CRITERIA):
    mask=Image.new('L',SIZE)
    draw=ImageDraw.Draw(mask)
    for x,y,nx,ny,width,role in paths:
        draw.line([pixel((x,y),criteria),pixel((nx,ny),criteria)],fill=255,
                  width=max(1,round(width/criteria.resolution_mm)))
    return mask


def path_chains(paths):
    """Preserve physical continuity across G-code segments and role changes."""
    chains=[]
    for path in paths:
        if not chains or math.dist(chains[-1][-1][2:4],path[:2])>0.002:
            chains.append([])
        chains[-1].append(path)
    return chains


def unsupported_runs(paths, previous, criteria=CRITERIA):
    tolerance=round(criteria.raster_tolerance_mm/criteria.resolution_mm)
    support=previous.filter(ImageFilter.MaxFilter(2*tolerance+1)) if tolerance else previous
    pixels=support.load()
    records=[]
    total=unsupported=0.0
    for chain in path_chains(paths):
        samples=[]
        for x,y,nx,ny,width,role in chain:
            length=math.hypot(nx-x,ny-y)
            count=max(1,math.ceil(length/criteria.resolution_mm))
            for i in range(count):
                t=(i+0.5)/count
                position=(x+(nx-x)*t,y+(ny-y)*t)
                ix,iy=pixel(position,criteria)
                supported=0<=ix<SIZE[0] and 0<=iy<SIZE[1] and bool(pixels[ix,iy])
                samples.append((supported,length/count,position,role))
        if not samples:
            continue
        total+=sum(s[1] for s in samples)
        unsupported+=sum(s[1] for s in samples if not s[0])
        closed=math.dist(chain[0][:2],chain[-1][2:4])<=0.002
        if closed and any(s[0] for s in samples):
            # A seam cannot divide an unsupported run into two shorter runs.
            anchor=next(i for i,s in enumerate(samples) if s[0])
            samples=samples[anchor:]+samples[:anchor]+[samples[anchor]]
        index=0
        while index<len(samples):
            if samples[index][0]:
                index+=1
                continue
            start=index
            while index<len(samples) and not samples[index][0]:
                index+=1
            run=samples[start:index]
            length=sum(s[1] for s in run)
            before=start>0 and samples[start-1][0]
            after=index<len(samples) and samples[index][0]
            a=samples[start-1][2] if before else run[0][2]
            b=samples[index][2] if after else run[-1][2]
            chord=math.dist(a,b)
            ratio=length/max(chord,criteria.resolution_mm)
            internal=all('infill' in s[3].lower() for s in run)
            bridge_limit=(criteria.maximum_internal_bridge_mm if internal else criteria.maximum_external_bridge_mm)
            short_local=(before or after) and length<=criteria.maximum_local_unanchored_run_mm+1e-9
            bridge=before and after and ratio<=criteria.maximum_bridge_curvature_ratio and length<=bridge_limit+1e-9
            records.append(dict(length_mm=round(length,5),start_xy_mm=list(a),end_xy_mm=list(b),
                                anchored_before=bool(before),anchored_after=bool(after),
                                curvature_ratio=round(ratio,4),roles=sorted({s[3] for s in run}),
                                classification='local-ledge' if short_local else 'anchored-bridge' if bridge else 'requires-review',
                                passes=bool(short_local or bridge)))
    return records,total,unsupported


def assess_toolpaths(layers, output, criteria=CRITERIA):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    previous=None
    records=[]
    hotspots=[]
    for index,layer in enumerate(layers):
        paths=model_paths(layer)
        if not paths:
            raise ValueError('printability screening requires model extrusion on every layer')
        current=deposition_mask(paths,criteria)
        runs,total,unsupported=([],sum(math.dist(p[:2],p[2:4]) for p in paths),0.0) if previous is None else unsupported_runs(paths,previous,criteria)
        failures=[r for r in runs if not r['passes']]
        record=dict(index=index,z_mm=layer['z'],model_path_length_mm=round(total,4),
                    centerline_without_previous_plastic_mm=round(unsupported,4),
                    maximum_unsupported_run_mm=max((r['length_mm'] for r in runs),default=0),
                    runs=runs,passes=not failures)
        records.append(record)
        if failures:
            tile=Image.new('RGB',SIZE,'#17212b')
            tile.paste('#77818a',mask=current)
            draw=ImageDraw.Draw(tile)
            for run in failures:
                draw.line([pixel(run['start_xy_mm']),pixel(run['end_xy_mm'])],fill='#ff6655',width=3)
            banner=Image.new('RGB',(SIZE[0],SIZE[1]+25),'#17212b')
            banner.paste(tile,(0,25))
            ImageDraw.Draw(banner).text((10,5),f"Layer {index+1} Z {layer['z']:.2f} mm | red: support review",fill='white')
            hotspots.append((max(r['length_mm'] for r in failures),index,banner))
        previous=current
    chosen=sorted(sorted(hotspots,key=lambda x:(-x[0],x[1]))[:12],key=lambda x:x[1])
    if chosen:
        sheet=Image.new('RGB',(SIZE[0],(SIZE[1]+25)*len(chosen)),'#17212b')
        for index,(_,_,tile) in enumerate(chosen):
            sheet.paste(tile,(0,index*(SIZE[1]+25)))
        sheet.save(output/'support-hotspots.png')
    result=dict(schema_version=1,criteria=asdict(criteria),
                method='ordered G-code centerline samples against previous deposited bead footprints; one-cell raster tolerance',
                limitation='digital screen only; cooling, adhesion, strength and surface quality require a physical trial',
                passes=all(r['passes'] for r in records),
                failing_layers=[r['index'] for r in records if not r['passes']],layers=records,
                summary=dict(layer_count=len(records),
                    model_path_length_mm=round(sum(r['model_path_length_mm'] for r in records),3),
                    unsupported_centerline_mm=round(sum(r['centerline_without_previous_plastic_mm'] for r in records),3),
                    unaccepted_run_count=sum(sum(not v['passes'] for v in r['runs']) for r in records),
                    accepted_bridge_count=sum(sum(v['classification']=='anchored-bridge' for v in r['runs']) for r in records)))
    (output/'printability.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


def assess_face_detail(layers, spec, output):
    """Verify named solid/empty facial witnesses in actual deposited layers.

    This detects filled-in recesses and lost noses even when the whole head
    still has a nonempty contour. It is not a complete surface fidelity test.
    """
    from .components.elves import ELF_LIBRARY,resolve_elf
    from .components.elves_v2 import point
    masks={}
    records=[]
    for instance in spec.instances:
        if instance.version!=10:
            continue
        plan=resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        atoms={a['role']:a for a in plan['atoms']}
        frame=atoms['cranium']['frame_mm']
        witnesses=[]
        for role in ('left_eye_socket','right_eye_socket','mouth_line'):
            cutter=atoms[role]
            x,y,z=cutter['location']
            witnesses.append((role,[x,y+cutter['dimensions'][1]/2-0.12,z],False))
        nose=atoms['nose_plane']['location']
        witnesses.extend([('nose',[nose[0],nose[1]-0.03,nose[2]-0.15],True),
                          ('brow_fill',plan['face_landmarks']['brow_fill_probe_local'],True)])
        for feature,local,material in witnesses:
            world=point(frame,local)
            index=next((i for i,l in enumerate(layers) if l['z']>=world[2]),None)
            if index is None:
                records.append(dict(instance_id=instance.instance_id,feature=feature,passes=False,reason='missing layer'))
                continue
            if index not in masks:
                masks[index]=deposition_mask(model_paths(layers[index]))
            ix,iy=pixel(world[:2])
            points=[(ix,iy),(ix-1,iy),(ix+1,iy),(ix,iy-1),(ix,iy+1)]
            count=sum(bool(masks[index].getpixel(p)) for p in points)
            passes=count>=3 if material else count<=2
            records.append(dict(instance_id=instance.instance_id,feature=feature,world_mm=world,
                                layer_index=index,layer_z_mm=layers[index]['z'],
                                expected='plastic' if material else 'open recess',deposited_samples=count,total_samples=5,
                                passes=passes))
    result=dict(method='five 0.025 mm raster witnesses in the deposited layer containing each named face landmark',
                limitation='local feature witnesses; inspect the complete face preview and a physical trial',
                applicable=bool(records),passes=all(r['passes'] for r in records),features=records)
    (Path(output)/'face-layer-evidence.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result
