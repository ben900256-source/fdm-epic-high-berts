import json
from pathlib import Path

from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.sergeant_helmets import sergeant_helmet, larger_sergeant_helmet

ROOT=Path(__file__).resolve().parent.parent


def test_sergeants_share_winged_helmet_and_preserve_approved_crown():
    definitions=catalog()
    parent=definitions['aurelian.helmet@5']
    golden=json.loads((ROOT/'tests/fixtures/sergeant-helmet-v1-golden.json').read_text())
    for _ in range(2):
        d=sergeant_helmet(parent,seed=1001)
        assert d.sha256==definitions[d.reference].sha256==golden[d.reference]
    p=d.to_dict()['parameters']; old=parent.to_dict()['parameters']
    assert p['atoms'][:len(old['atoms'])]==old['atoms']
    assert p['operations'][:len(old['operations'])]==old['operations']
    for k,v in old['landmarks'].items():assert p['landmarks'][k]==v
    large=larger_sergeant_helmet(parent,seed=1001)
    golden2=json.loads((ROOT/'tests/fixtures/sergeant-helmet-v2-golden.json').read_text())
    assert larger_sergeant_helmet(parent,seed=1001).sha256==large.sha256==definitions[large.reference].sha256==golden2[large.reference]
    assert large.to_dict()['parameters']['atoms'][:len(old['atoms'])]==old['atoms']
    assert large.to_dict()['parameters']['ornament_scale']['feather_length']==1.5
    for name in ('elf-archer-sergeant.json','spearmen/10-hawk-sergeant.json'):
        slots={p['instance_id']:p for p in load_model(ROOT/'specs/models'/name,definitions)['placements']}
        assert slots['helmet']['part']==large.reference
        assert slots['helmet']['mount']==slots['head']['mount']==slots['crest']['mount']
