"""Pin the first visual pass of all remaining Warmaster High Elf roles."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.core import ComponentDefinition,component_digest
from fdm_sculpt.components.parts import validate_part,resolve_assembly
from fdm_sculpt.components.elves_v2 import identity,multiply,rotation,translation,point
from fdm_sculpt.components.army_expansion import all_parts,PREFIX,SEED,CURRENT_REVISIONS

class Definitions(dict):
    def __missing__(self,ref):
        self[ref]=validate_part(ComponentDefinition.from_dict(json.loads((ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text())))
        return self[ref]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def generate(seed=SEED):
    defs=Definitions();parts=all_parts(seed)
    for part in parts:
        path=ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
        if path.exists():
            assert ComponentDefinition.from_dict(json.loads(path.read_text())).sha256==part.sha256,part.reference+' is immutable; create a new revision'
        else:write(path,part.to_dict())
        defs[part.reference]=part
    specs={}
    def put(items,name,ref,at=(0,0,0),angles=(0,0,0),matrix=None):
        if ref.startswith('expansion-'):ref='aurelian.'+ref+'@1'
        ref=CURRENT_REVISIONS.get(ref,ref)
        items.append(dict(instance_id=name,part=ref,definition_sha256=defs[ref].sha256,
                          mount=matrix if matrix is not None else multiply(translation(at),rotation(angles))))
    def add_upper(items,kind,prefix,at,angles=(0,0,0),mounted=False):
        frame=multiply(translation(at),rotation(angles))
        def local(slot,ref,offset=(0,0,0),turn=(0,0,0)):
            put(items,prefix+'/'+slot,ref,matrix=multiply(frame,multiply(translation(offset),rotation(turn))))
        local('torso','aurelian.readable-torso-trial@1')
        if kind not in ('mage','driver','crew'):local('chest','aurelian.readable-chest-plate-trial@1')
        helm='aurelian.swordmaster-sergeant-helmet-accepted-r2@5' if kind=='general' else 'aurelian.readable-helmet-trial@5'
        for slot,ref in [('head','aurelian.readable-head-trial@5'),('helmet',helm)]:local(slot,ref,(0,0,2))
        if kind!='mage':local('crest','aurelian.crest@7',(0,0,2))
        local('arms','expansion-'+kind+'-arms')
        if kind in ('general','hero','mage'):
            local('regalia','expansion-'+kind+('-riding-regalia' if mounted else '-regalia'))
            arm=defs[PREFIX+kind+'-arms@1'].to_dict()['parameters']['landmarks']
            if kind=='mage':local('staff','expansion-mage-staff',arm['right_grip'],(0,-7,0))
            else:
                local('sword','expansion-command-sword',arm['right_grip'],(5,22,3) if kind=='general' else (4,145,-12))
                grip=arm['left_grip'];shield=[grip[0],grip[1]-.60,grip[2]-.75]
                local('shield','aurelian.shield@6',shield,(0,0,-8))
                local('shield-insignia','aurelian.readable-insignia-trial@6',shield,(0,0,-8))
        else:local('coat','expansion-reaver-coat')
    def legs(items,prefix,at,angles=(0,0,0),pose='c'):
        for side in ('left','right'):
            put(items,prefix+'/'+side+'-leg',f'aurelian.{side}-leg-{pose}@6',at,angles)
    def ground_character(kind):
        items=[];put(items,'base','aurelian.glue-footing@1');put(items,'terrain','aurelian.terrain-soil-gallery@5',(0,0,1))
        legs(items,'character',(0,0,6.2));add_upper(items,kind,'character',(0,0,6.2))
        if kind!='mage':put(items,'character/mail-skirt','aurelian.readable-mail-trial@3',(0,0,6.2))
        return items
    def save(name,label,items,role):
        spec=resolve_assembly(dict(schema_version=1,assembly_id='aurelian-expansion-'+name,label=label+' (visual-only)',placements=items),defs)
        specs[name]=dict(spec=spec,role=role,path='specs/army-expansion/'+name+'.json')
        write(ROOT/specs[name]['path'],spec)
    for kind in ('general','hero','mage'):
        save(kind,kind.capitalize()+' on foot',ground_character(kind),kind)
    # Three mounted archer poses share the same horse, saddle and riding legs.
    reavers=[]
    archer=json.loads((ROOT/'specs/elf-archer.json').read_text())
    for i,angle in enumerate((-18,0,20),1):
        x=(i-2)*9;prefix=f'reaver-{i:02}'
        put(reavers,prefix+'/base','aurelian.cavalry-base-body-6x12@1',(x,0,0))
        put(reavers,prefix+'/terrain','aurelian.cavalry-soil-6x12@1',(x,0,2))
        for slot,ref in [('horse','aurelian.dragon-prince-horse@7'),('saddle','aurelian.dragon-prince-saddle@1'),('riding-legs','aurelian.dragon-prince-riding-legs@1'),('tack','expansion-light-horse-tack')]:
            put(reavers,prefix+'/'+slot,ref,(x,0,2))
        body=multiply(translation([x,0,10]),rotation([0,0,angle]))
        put(reavers,prefix+'/coat','expansion-reaver-coat',matrix=body)
        for p in archer['placements']:
            if '/' not in p['instance_id']:continue
            slot=p['instance_id'].split('/')[1]
            if slot in ('left-leg','right-leg','tunic'):continue
            mount=multiply(body,multiply(translation([0,0,-6.2]),p['mount']))
            put(reavers,prefix+'/'+slot,p['part'],matrix=mount)
    save('reavers','Reavers - three light cavalry archers',reavers,'reavers')
    def creature(name,kind=None):
        items=[];base='dragon-base' if name=='dragon' else 'creature-base'
        put(items,'base','expansion-'+base)
        put(items,'creature','expansion-'+('giant-eagle' if name=='eagle' else name),(0,0,1.2))
        if kind:
            creature_ref=PREFIX+('giant-eagle' if name=='eagle' else name)+'@1'
            seat=defs[creature_ref].to_dict()['parameters']['landmarks']['saddle']
            seat=[seat[0],seat[1],seat[2]+1.2]
            put(items,'rider/saddle-and-legs','expansion-'+name+'-seat',seat)
            add_upper(items,kind,'rider',[seat[0],seat[1],seat[2]+2.05],mounted=True)
        return items
    save('giant-eagle','Giant Eagle - perched with swept wings',creature('eagle'),'giant-eagles')
    save('dragon-rider','Dragon Rider - grounded dragon',creature('dragon','hero'),'dragon-rider')
    for mount in ('eagle','dragon'):
        for kind in ('general','hero','mage'):
            save(kind+'-on-'+mount,kind.capitalize()+' on '+mount.capitalize(),creature(mount,kind),kind+'-on-'+mount)
    def chariot(kind=None):
        items=[];put(items,'base','expansion-chariot-base')
        put(items,'vehicle','expansion-chariot',(0,0,1.2))
        put(items,'reins','expansion-chariot-reins',(0,0,1.2))
        for i,x in enumerate((-2.25,2.25),1):
            for slot,ref in [('horse','aurelian.dragon-prince-horse@7'),('tack','expansion-light-horse-tack')]:
                put(items,f'team-{i}/'+slot,ref,(x,-4.4,1.2))
        for prefix,who,y in [('driver','driver',2.3),('passenger',kind or 'hero',5.0)]:
            at=(0,y,9.2);legs(items,prefix,at);add_upper(items,who,prefix,at)
            if who not in ('mage','driver'):put(items,prefix+'/mail-skirt','aurelian.readable-mail-trial@3',at)
        return items
    save('chariot','Chariot - two-horse team and crew',chariot(),'chariots')
    for kind in ('general','hero','mage'):
        save(kind+'-on-chariot',kind.capitalize()+' on chariot',chariot(kind),kind+'-on-chariot')
    artillery=[];put(artillery,'base','expansion-artillery-base');put(artillery,'engine','expansion-bolt-thrower',(0,-1.1,1.2))
    for i,(x,y,angle) in enumerate([(-3.35,1.3,65),(4.1,1.7,-65)],1):
        at=(x,y,6.4);legs(artillery,f'crew-{i}',at,(0,0,angle))
        add_upper(artillery,'crew',f'crew-{i}',at,(0,0,angle))
        if i==2:put(artillery,f'crew-{i}/spare-bolt','expansion-loader-bolt',at,(0,0,angle))
    save('bolt-thrower','Elven Bolt Thrower - engine and two crew',artillery,'elven-bolt-thrower')
    # A gallery of the eight main roles. Mount alternatives have their own viewer entries.
    overview=[]
    layout=[('reavers',0,0),('chariot',32,0),('bolt-thrower',56,0),('giant-eagle',0,28),('dragon-rider',25,28),('general',48,28),('hero',56,28),('mage',64,28)]
    for name,x,y in layout:
        for p in specs[name]['spec']['placements']:
            item=deepcopy(p);item['instance_id']=name+'/'+item['instance_id'];item['mount']=multiply(translation([x,y,0]),item['mount']);overview.append(item)
    gallery=resolve_assembly(dict(schema_version=1,assembly_id='aurelian-army-expansion',label='High Elf army expansion - first visual pass',placements=overview),defs)
    write(ROOT/'specs/elf-army-expansion.json',gallery)
    golden={p.reference:p.sha256 for p in parts}
    write(ROOT/'tests/fixtures/army-expansion-golden.json',golden)
    record=dict(schema_version=1,seed=seed,export_scale=1.3,status='visual-only; all new variants unprinted',digitally_validated=False,
        overview='specs/elf-army-expansion.json',assemblies=[dict(path=v['path'],role=v['role'],id=v['spec']['assembly_id']) for v in specs.values()],
        components=golden,shared_parts=sorted(set(p['part'] for v in specs.values() for p in v['spec']['placements'])-set(golden)),
        coverage=['reavers','chariots','giant-eagles','dragon-rider','elven-bolt-thrower','general','hero','mage'],
        mounts={kind:['eagle','dragon','chariot'] for kind in ('general','hero','mage')},
        notes=['New visual designs are not included in the September Cults3D upload kit.','Locked spearmen, previous component revisions and accepted army recipes are unchanged.','Local Exact details and overlapping primitive outputs only; no manufacturing fusion, repeat geometry build, mesh gate or slicing.'])
    write(ROOT/'specs/army-expansion-index.json',record)
    print(json.dumps(dict(new_parts=len(parts),assemblies=len(specs),shared_parts=len(record['shared_parts']),overview_parts=len(overview)),indent=2))
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',required=True,type=int);args=parser.parse_args();generate(args.seed)
