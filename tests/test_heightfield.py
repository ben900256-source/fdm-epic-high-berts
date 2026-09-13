from collections import Counter
from copy import deepcopy

import pytest

from fdm_sculpt.atelier import engine_hash
from fdm_sculpt.components.heightfield import grid_mesh, sample_surface, validate_grid
from fdm_sculpt.components.parts import cache_key,catalog
from fdm_sculpt.components.terrain import terrain_surface


def test_sampled_mesh_is_deterministic_and_shares_its_boundary():
    grid=sample_surface(width=1,length=1,style='soil',feature_scale=1,relief_height=.25,
                        density=1,seed=1001,boots=[],spacing=.1)
    vertices,faces,top=grid_mesh(grid)
    assert (vertices,faces,top)==grid_mesh(deepcopy(grid))
    directed=Counter((a,b) for face in faces for a,b in zip(face,face[1:]+face[:1]))
    assert all(count==1 and directed[(b,a)]==1 for (a,b),count in directed.items())
    assert all(vertices[i][2]==-.15 for i in range(len(vertices)//2,len(vertices)))
    for face in faces[:top]:
        a,b,c=[vertices[i] for i in face]
        assert (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0


def test_soil_and_sand_are_continuous_fields_without_rounded_operands():
    parts=[terrain_surface('test.field',1,style=style,seed=1001,width=1,length=1) for style in ('soil','sand')]
    assert parts[0].sha256!=parts[1].sha256
    for d in parts:
        p=d.to_dict()['parameters']
        assert p['operations']==[]
        assert [a['primitive'] for a in p['atoms']]==['heightfield']
        heights=p['atoms'][0]['grid']['heights']
        assert len({v for row in heights for v in row})>100
        # Adjacent samples stay continuous; there are no independent lump seams.
        assert max(abs(a-b) for row in heights for a,b in zip(row,row[1:]))<.08


def test_heightfield_engine_does_not_invalidate_primitive_caches(monkeypatch):
    from fdm_sculpt import atelier
    definitions=catalog()
    figure=definitions['aurelian.head@12']
    body=definitions['aurelian.base-body-4x5@1']
    terrain=definitions['aurelian.terrain-soil-gallery@3']
    before={d.reference:cache_key(d,engine_hash(d)) for d in (figure,body,terrain)}
    original=atelier.file_hash
    monkeypatch.setattr(atelier,'file_hash',lambda path:'changed' if path.name=='atelier_heightfield_blender.py' else original(path))
    assert cache_key(figure,engine_hash(figure))==before[figure.reference]
    assert cache_key(body,engine_hash(body))==before[body.reference]
    assert cache_key(terrain,engine_hash(terrain))!=before[terrain.reference]


@pytest.mark.parametrize('grid',[
    dict(width=1,length=1,bottom=0,heights=[[1,1],[1,float('nan')]]),
    dict(width=1,length=1,bottom=0,heights=[[1,1],[1]]),
    dict(width=1,length=1,bottom=0,heights=[[1,1],[1,-1]])])
def test_bad_sample_grids_rejected(grid):
    with pytest.raises(ValueError):validate_grid(grid)
