from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly
from fdm_sculpt.atelier import prepare
from fdm_sculpt.components.core import component_digest
from fdm_sculpt.components.parts import catalog, cache_key, isolated_part, resolve_assembly
from fdm_sculpt.components.terrain import base_body, terrain_surface, boot_regions, write_definition

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope='module')
def definitions():
    return catalog()


def test_all_presets_repeat_and_resolve(definitions):
    golden=json.loads((ROOT/'tests/fixtures/terrain-v1-golden.json').read_text())
    golden.update(json.loads((ROOT/'tests/fixtures/terrain-v2-golden.json').read_text()))
    golden.update(json.loads((ROOT/'tests/fixtures/terrain-v3-golden.json').read_text()))
    golden.update(json.loads((ROOT/'tests/fixtures/archer-natural-ground-v1-golden.json').read_text()))
    golden.update(json.loads((ROOT/'tests/fixtures/visible-archer-soil-v1-golden.json').read_text()))
    presets=json.loads((ROOT/'specs/terrain-presets.json').read_text())
    for p in presets:
        recipe=base_body if p['kind']=='body' else terrain_surface
        a=recipe(p['component_id'],p['revision'],**p['parameters'])
        b=recipe(p['component_id'],p['revision'],**p['parameters'])
        assert a.sha256==b.sha256==golden[a.reference]==definitions[a.reference].sha256
        resolve_assembly(isolated_part(a.reference,definitions),definitions)


@pytest.mark.parametrize('kwargs',[
    dict(magnet='3x1'),dict(thickness=1.8),dict(centers=[[1,0]]),
    dict(width=20,magnet='3x1',centers=[[0,0],[3.3,0]]),
    dict(width=float('nan')),dict(thickness=-1),dict(magnet='none',centers=[[0,0]])])
def test_bad_stock_rejected(kwargs):
    with pytest.raises(ValueError):base_body('test.body',1,**kwargs)


def test_pocket_contract(definitions):
    for width,diameter,centers in [(4,2.2,[[0,0]]),(20,3.2,[[-6,0],[6,0]])]:
        p=definitions[f'aurelian.base-body-{width}x5@1'].to_dict()['parameters']
        assert p['atoms'][0]['dimensions']==[width,5,2]
        assert p['recipe']['centers']==centers
        for a in p['atoms'][1:]:
            assert a['radius']*2==diameter
            assert a['bevel']==0
            assert a['location'][2]-a['depth']/2<0
            assert a['location'][2]+a['depth']/2==pytest.approx(1.1)
            assert 2-(a['location'][2]+a['depth']/2)==pytest.approx(.9)


def test_seed_and_cache_independence(definitions,tmp_path):
    a=terrain_surface('test.surface',1,seed=1001)
    b=terrain_surface('test.surface',1,seed=1002)
    assert a.to_dict()['parameters']['atoms']!=b.to_dict()['parameters']['atoms']
    assert cache_key(a,'engine')!=cache_key(b,'engine')
    original=base_body('test.body',1)
    alternative=base_body('test.body',2,magnet='none')
    assert cache_key(original,'engine')!=cache_key(alternative,'engine')
    definitions=dict(definitions)
    for part in (a,original,alternative):definitions[part.reference]=part
    assembly=isolated_part('aurelian.head@12',definitions)
    for name,part in [('body',original),('terrain',a)]:
        p=isolated_part(part.reference,definitions)['placements'][0]
        assembly['placements'].append(dict(p,instance_id=name))
    first=prepare(assembly,seed=1001,cache=tmp_path,definitions=definitions)
    definitions[b.reference]=b
    assembly['placements'][1].update(part=alternative.reference,definition_sha256=alternative.sha256)
    assembly['placements'][2]['definition_sha256']=b.sha256
    second=prepare(assembly,seed=1002,cache=tmp_path,definitions=definitions)
    assert first['assets']['aurelian.head@12']['key']==second['assets']['aurelian.head@12']['key']
    assert first['assets'][a.reference]['key']!=second['assets'][b.reference]['key']
    write_definition(a,tmp_path)
    write_definition(a,tmp_path)
    with pytest.raises(ValueError):
        write_definition(terrain_surface('test.surface',1,seed=42),tmp_path)


def test_migrated_figure_placement_and_boot_clearance(definitions):
    baseline=json.loads((ROOT/'tests/fixtures/terrain-migration-baseline.json').read_text())
    for name,hashes in baseline.items():
        layout=load_assembly(ROOT/f'specs/{name}.json',definitions)
        placements={p['instance_id']:p for p in layout['placements']}
        for instance,digest in hashes.items():
            original=deepcopy(placements[instance])
            original['mount'][2][3]-=1
            original['mount']=[[round(v,8) for v in row] for row in original['mount']]
            assert component_digest(original)==digest
        for p in placements.values():
            definition=definitions[p['part']]
            if definition.family!='base-body':continue
            terrain=placements[p['instance_id']+'-terrain']
            params=definitions[terrain['part']].to_dict()['parameters']
            assert terrain['mount'][2][3]-p['mount'][2][3]==2
            width=params['recipe']['width']
            boxes=boot_regions(layout['placements'],definitions,p['mount'])
            boxes=[b for b in boxes if b[0]<width/2 and b[2]>-width/2 and b[1]<2.5 and b[3]>-2.5]
            natural=name in ('elf-archer','elf-unit-archers','elf-archer-variants','elf-archer-sergeant')
            assert params['recipe']['boots']==([] if natural else boxes)
            assert len(params['atoms'])==1 and params['atoms'][0]['primitive']=='heightfield'
            assert params['operations']==[]
            grid=params['atoms'][0]['grid']
            assert grid['bottom']==-.15 and grid['width']==width and grid['length']==5
            for j,row in enumerate(grid['heights']):
                y=-2.5+5*j/(len(grid['heights'])-1)
                for i,height in enumerate(row):
                    x=-width/2+width*i/(len(row)-1)
                    if any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in boxes):
                        if natural:
                            assert .012<height<=params['recipe']['relief_height']
                        else:
                            assert height<=.015


def test_invalid_seed_and_parameters():
    for seed in (True,None,1.5):
        with pytest.raises(ValueError):terrain_surface('test.surface',1,seed=seed)
    for kw in (dict(density=0),dict(style='water'),dict(feature_scale=float('inf'))):
        with pytest.raises(ValueError):terrain_surface('test.surface',1,seed=1001,**kw)


@pytest.mark.integration
def test_saved_terrain_revisions():
    root=os.environ.get('TERRAIN_PROOF_ROOT')
    if not root:pytest.skip('set TERRAIN_PROOF_ROOT to the completed terrain review output root')
    root=Path(root)
    golden=json.loads((ROOT/'tests/fixtures/terrain-v3-golden.json').read_text())
    checked=set()
    for output in [root/'terrain-gallery-v3',*root.glob('elf*-terrain-v3')]:
        job=json.loads((output/'assembly-job.json').read_text())
        provenance=json.loads((output/'saved-provenance.json').read_text())
        assert provenance['passes'] and all(provenance['checks'].values())
        assert not json.loads((output/'visual-review.json').read_text())['digitally_validated']
        for ref,asset in job['assets'].items():
            if ref in golden:
                assert asset['definition']['version']==(1 if 'base-body' in ref else 3)
                checked.add(ref)
    assert checked==set(golden)
    geometry=json.loads((root/'terrain-geometry-check.json').read_text())
    assert geometry['passes'] and set(geometry['parts'])==set(golden)
    assert all(all(p['checks'].values()) for p in geometry['parts'].values())
