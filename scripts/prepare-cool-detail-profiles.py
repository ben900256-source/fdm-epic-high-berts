"""Create new preset copies in a fresh output folder; never modify installed inputs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.prusa import read_settings


def prepare(datadir,output):
    recipe=json.loads((ROOT/'specs/prusa-cool-detail-v1.json').read_text())
    if output.exists() and any(output.iterdir()):raise ValueError('Use a fresh output directory')
    output.mkdir(parents=True,exist_ok=True)
    records=[];bundle=[]
    for category in ('print','filament'):
        item=recipe[category];source=datadir/category/(item['source']+'.ini')
        original=source.read_bytes();values=read_settings(original.decode('utf-8-sig'))
        values.update(item['overrides'])
        # Each copy retains the original's vendor inheritance and all saved
        # values, so changing the old custom preset later does not edit this one.
        values[category+'_settings_id']=item['name'] if category=='print' else '"'+item['name']+'"'
        note='Experimental 0.25 mm miniature cooling/detail profile v1; based on '+item['source']+'.'
        values['notes' if category=='print' else 'filament_notes']=note
        text=''.join(f'{k} = {v}\n' for k,v in sorted(values.items()))
        folder=output/category;folder.mkdir()
        path=folder/(item['name']+'.ini');path.write_text(text,encoding='utf-8')
        bundle.extend([f'[{category}:{item["name"]}]\n',text,'\n'])
        records.append(dict(category=category,name=item['name'],source=str(source),
                            source_sha256=hashlib.sha256(original).hexdigest(),
                            prepared=str(path.resolve()),prepared_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (output/'Epic-Cool-Detail-v1-config-bundle.ini').write_text(''.join(bundle),encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps(dict(recipe='specs/prusa-cool-detail-v1.json',profiles=records),indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datadir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.datadir,args.output)
