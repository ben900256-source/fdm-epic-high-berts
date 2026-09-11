from PIL import Image,ImageDraw
from fdm_sculpt.printability import CRITERIA,SIZE,pixel,unsupported_runs,assess_toolpaths


def rectangle(bounds):
    mask=Image.new('L',SIZE)
    a,b=pixel(bounds[:2]),pixel(bounds[2:])
    ImageDraw.Draw(mask).rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),fill=255)
    return mask


def path(a,b,role='External perimeter'):
    return (*a,*b,0.25,role)


def test_vertical_wall_supported_by_deposited_plastic():
    runs,_,missing=unsupported_runs([path((-1,0),(1,0))],rectangle((-2,-.15,2,.15)))
    assert not runs and missing==0


def test_free_floating_path_is_rejected():
    runs,_,_=unsupported_runs([path((-1,1),(1,1))],rectangle((-2,-.15,2,.15)))
    assert not any(r['passes'] for r in runs)


def test_short_two_ended_bridge_and_long_cantilever():
    mask=rectangle((-1,-.2,-.25,.2))
    ImageDraw.Draw(mask).rectangle((pixel((.25,.2)),pixel((1,-.2))),fill=255)
    runs,_,_=unsupported_runs([path((-.8,0),(.8,0))],mask)
    assert len(runs)==1 and runs[0]['classification']=='anchored-bridge'
    runs,_,_=unsupported_runs([path((-.8,0),(.8,0))],rectangle((-1,-.2,-.25,.2)))
    assert any(not r['passes'] for r in runs)


def test_closed_loop_seam_cannot_hide_an_unsupported_arc():
    paths=[path((0,0),(.6,0)),path((.6,0),(.6,.6)),path((.6,.6),(0,.6)),path((0,.6),(0,0))]
    runs,_,_=unsupported_runs(paths,rectangle((.5,-.1,.7,.7)))
    assert len(runs)==1 and runs[0]['length_mm']>1.4 and not runs[0]['passes']


def test_first_layer_is_bed_supported_but_second_must_have_plastic(tmp_path):
    layers=[dict(z=.14,paths=[path((-1,0),(1,0))]),dict(z=.19,paths=[path((-1,1),(1,1))])]
    result=assess_toolpaths(layers,tmp_path)
    assert not result['passes'] and result['failing_layers']==[1]
    assert (tmp_path/'support-hotspots.png').is_file()
    assert CRITERIA.removable_support_target==0


def test_support_estimate_separates_brim_and_respects_extrusion_modes():
    from fdm_sculpt.prusa import filament_by_role
    text='\n'.join(['M83','G1 X10 E10',';LAYER_CHANGE',';TYPE:Skirt/Brim','G1 X20 E2',
        ';TYPE:External perimeter','G1 X30 E3','G1 E-1','G1 E1',';TYPE:Support material',
        'G91','G1 X2 E4','G90','M82','G92 E0',';TYPE:Support material interface',
        'G1 X40 E5','G1 X41 E4','G1 E5',';TYPE:Solid infill','G1 X42 E7'])
    assert filament_by_role(text)=={'model':5.0,'support':9.0,'adhesion':2.0}


def test_face_screen_rejects_missing_noses_and_filled_eye_sockets(tmp_path):
    from pathlib import Path
    from fdm_sculpt.printability import assess_face_detail
    from fdm_sculpt.regiment_spec import RegimentSpec
    spec=RegimentSpec.load(Path(__file__).resolve().parent.parent/'specs/elf-spearman-proof-v10.json')
    empty=assess_face_detail([dict(z=13,paths=[])],spec,tmp_path)
    assert not empty['passes'] and len(empty['features'])==25
    assert all(not r['passes'] for r in empty['features'] if r['expected']=='plastic')
    filled=[path((-10,y/4),(10,y/4)) for y in range(-12,13)]
    solid=assess_face_detail([dict(z=13,paths=filled)],spec,tmp_path)
    assert not solid['passes']
    assert all(not r['passes'] for r in solid['features'] if r['expected']=='open recess')
