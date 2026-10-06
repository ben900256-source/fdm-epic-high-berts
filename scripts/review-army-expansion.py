"""Build cached isolated parts and assembled visual reviews; never manufacture."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fdm_sculpt import atelier
from fdm_sculpt.components.army_expansion import CURRENT_REVISIONS
from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.parts import isolated_part,validate_part
class Definitions(dict):
    def __missing__(self,ref):
        self[ref]=validate_part(ComponentDefinition.from_dict(json.loads((ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text())))
        return self[ref]
def run(output,seed,only=None):
    if output.exists():raise ValueError('Use a fresh review directory')
    output.mkdir(parents=True);definitions=Definitions();index=json.loads((ROOT/'specs/army-expansion-index.json').read_text())
    files=[index['overview']]+[r['path'] for r in index['assemblies']]
    if only:
        known={Path(file).stem for file in files}
        if set(only)-known:raise ValueError('Unknown assemblies: '+str(set(only)-known))
        files=[file for file in files if Path(file).stem in only]
    used={p['part'] for file in files for p in json.loads((ROOT/file).read_text())['placements']}
    records=[]
    for name in ('giant-eagle','dragon','chariot','bolt-thrower'):
        reference=CURRENT_REVISIONS.get('aurelian.expansion-'+name+'@1','aurelian.expansion-'+name+'@1')
        if reference not in used:continue
        print('ISOLATED',reference,flush=True)
        result=atelier.compose(isolated_part(reference,definitions),seed=seed,output=output/'parts'/name,definitions=definitions)
        records.append(dict(kind='part',name=name,compiled=result['compiled_parts'],reused=result['reused_parts']))
    for file in files:
        data=json.loads((ROOT/file).read_text());print('ASSEMBLY',data['assembly_id'],flush=True)
        result=atelier.compose(data,seed=seed,output=output/'assemblies'/Path(file).stem,definitions=definitions)
        records.append(dict(kind='assembly',name=data['assembly_id'],compiled=result['compiled_parts'],reused=result['reused_parts']))
        (output/'review-record.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('VISUAL_REVIEWS_COMPLETE',len(records),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--only',nargs='+',help='Assembly file stems to refresh, reusing all cached parts')
    args=parser.parse_args();run(args.output.resolve(),args.seed,args.only)
