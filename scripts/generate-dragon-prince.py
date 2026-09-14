"""Generate a visual Dragon Prince cavalry prototype without Blender."""
import json
from pathlib import Path
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.dragon_princes import cavalry_parts,open_face_barding
from fdm_sculpt.components.dragon_prince_reference import reference_parts,connected_head_parts,scale_helmets,upright_helmets,swept_visor,larger_shield,great_shield,flexed_steed,scalp_barding,routed_reins,gem_shield,scaled_shield,dense_scaled_shield,supported_lance_seal,flush_reins,angular_pauldrons,fitted_reins,bridle_fitted_reins,tapestry_lance,heroic_steed
from fdm_sculpt.components.spearmen import part,link
from fdm_sculpt.components.terrain import base_body,terrain_surface,write_definition
from fdm_sculpt.components.elves_v2 import multiply,translation
from fdm_sculpt.components.swordmaster_variants import rotation

ROOT=Path(__file__).resolve().parent.parent
def main():
    d=catalog();parts=cavalry_parts(d,1001)
    parts.extend([base_body('aurelian.cavalry-base-body-6x12',1,width=6,length=12,magnet='3x1'),
        terrain_surface('aurelian.cavalry-soil-6x12',1,width=6,length=12,feature_scale=1.4,relief_height=.35,seed=1001)])
    parts.append(part('dragon-prince-reins',[link('reins_front',[-.6,-4,6.8],[-1.1,-2.7,7.2],.12),link('reins_hand',[-1.1,-2.7,7.2],[-1.5,-1,8.4],.12)],{},1001))
    for p in parts:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    bard=open_face_barding(1001);write_definition(bard,ROOT/'fdm_sculpt/components/parts');d[bard.reference]=bard
    reference=reference_parts(d,1001)
    for p in reference:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    connected=connected_head_parts(d,1001)
    for p in connected:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    (ROOT/'tests/fixtures/dragon-prince-connected-heads-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in connected},indent=2)+'\n')
    scales=scale_helmets(d,1001)
    for p in scales:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    (ROOT/'tests/fixtures/dragon-prince-scale-helmets-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in scales},indent=2)+'\n')
    upright=upright_helmets(d,1001)
    for p in upright:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    (ROOT/'tests/fixtures/dragon-prince-upright-helmets-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in upright},indent=2)+'\n')
    visor=swept_visor(d,1001)
    write_definition(visor,ROOT/'fdm_sculpt/components/parts');d[visor.reference]=visor
    (ROOT/'tests/fixtures/dragon-prince-visor-golden.json').write_text(json.dumps({visor.reference:visor.sha256},indent=2)+'\n')
    shield=larger_shield(1001)
    write_definition(shield,ROOT/'fdm_sculpt/components/parts');d[shield.reference]=shield
    (ROOT/'tests/fixtures/dragon-prince-shield-golden.json').write_text(json.dumps({shield.reference:shield.sha256},indent=2)+'\n')
    steed=flexed_steed(1001)
    write_definition(steed,ROOT/'fdm_sculpt/components/parts');d[steed.reference]=steed
    (ROOT/'tests/fixtures/dragon-prince-flexed-horse-golden.json').write_text(json.dumps({steed.reference:steed.sha256},indent=2)+'\n')
    scalp=scalp_barding(d,1001)
    write_definition(scalp,ROOT/'fdm_sculpt/components/parts');d[scalp.reference]=scalp
    (ROOT/'tests/fixtures/dragon-prince-scalp-golden.json').write_text(json.dumps({scalp.reference:scalp.sha256},indent=2)+'\n')
    great=great_shield(1001)
    write_definition(great,ROOT/'fdm_sculpt/components/parts');d[great.reference]=great
    (ROOT/'tests/fixtures/dragon-prince-great-shield-golden.json').write_text(json.dumps({great.reference:great.sha256},indent=2)+'\n')
    reins=routed_reins(1001)
    write_definition(reins,ROOT/'fdm_sculpt/components/parts');d[reins.reference]=reins
    (ROOT/'tests/fixtures/dragon-prince-routed-reins-golden.json').write_text(json.dumps({reins.reference:reins.sha256},indent=2)+'\n')
    gem=gem_shield(1001)
    write_definition(gem,ROOT/'fdm_sculpt/components/parts');d[gem.reference]=gem
    (ROOT/'tests/fixtures/dragon-prince-gem-shield-golden.json').write_text(json.dumps({gem.reference:gem.sha256},indent=2)+'\n')
    scaled=scaled_shield(1001)
    write_definition(scaled,ROOT/'fdm_sculpt/components/parts');d[scaled.reference]=scaled
    (ROOT/'tests/fixtures/dragon-prince-scaled-shield-golden.json').write_text(json.dumps({scaled.reference:scaled.sha256},indent=2)+'\n')
    dense=dense_scaled_shield(1001)
    write_definition(dense,ROOT/'fdm_sculpt/components/parts');d[dense.reference]=dense
    (ROOT/'tests/fixtures/dragon-prince-dense-scaled-shield-golden.json').write_text(json.dumps({dense.reference:dense.sha256},indent=2)+'\n')
    seal=supported_lance_seal(1001)
    write_definition(seal,ROOT/'fdm_sculpt/components/parts');d[seal.reference]=seal
    (ROOT/'tests/fixtures/dragon-prince-supported-seal-golden.json').write_text(json.dumps({seal.reference:seal.sha256},indent=2)+'\n')
    fitted=[flush_reins(1001),angular_pauldrons(1001)]
    for p in fitted:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    (ROOT/'tests/fixtures/dragon-prince-fitted-reins-pauldrons-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in fitted},indent=2)+'\n')
    snug=fitted_reins(1001)
    write_definition(snug,ROOT/'fdm_sculpt/components/parts');d[snug.reference]=snug
    (ROOT/'tests/fixtures/dragon-prince-snug-reins-golden.json').write_text(json.dumps({snug.reference:snug.sha256},indent=2)+'\n')
    bridle=bridle_fitted_reins(1001)
    write_definition(bridle,ROOT/'fdm_sculpt/components/parts');d[bridle.reference]=bridle
    (ROOT/'tests/fixtures/dragon-prince-bridle-fitted-reins-golden.json').write_text(json.dumps({bridle.reference:bridle.sha256},indent=2)+'\n')
    tapestry=tapestry_lance(1001)
    write_definition(tapestry,ROOT/'fdm_sculpt/components/parts');d[tapestry.reference]=tapestry
    (ROOT/'tests/fixtures/dragon-prince-tapestry-lance-golden.json').write_text(json.dumps({tapestry.reference:tapestry.sha256},indent=2)+'\n')
    heroic=heroic_steed(1001)
    write_definition(heroic,ROOT/'fdm_sculpt/components/parts');d[heroic.reference]=heroic
    (ROOT/'tests/fixtures/dragon-prince-heroic-steed-golden.json').write_text(json.dumps({heroic.reference:heroic.sha256},indent=2)+'\n')
    def placement(slot,ref,mount):return dict(instance_id=slot,part=ref,definition_sha256=d[ref].sha256,mount=mount)
    placements=[placement('base','aurelian.cavalry-base-body-6x12@1',translation([0,0,0])),placement('terrain','aurelian.cavalry-soil-6x12@1',translation([0,0,2]))]
    for name in ('horse','barding','saddle','riding-legs','reins'):
        ref={'barding':'aurelian.dragon-prince-barding@8','horse':'aurelian.dragon-prince-horse@5','reins':'aurelian.dragon-prince-reins@6'}.get(name,'aurelian.dragon-prince-'+name+'@1')
        placements.append(placement('prince-01/'+name,ref,translation([0,0,2])))
    torso=translation([0,0,10]);head=translation([0,0,12])
    for slot,ref in [('torso','aurelian.torso@2'),('cuirass','aurelian.swordmaster-cuirass@1'),('pauldrons','aurelian.dragon-prince-winged-pauldrons@2'),('waist-wrap','aurelian.cloth-waist-wrap@1'),('left-arm','aurelian.dragon-prince-left-arm@1'),('right-arm','aurelian.dragon-prince-right-arm@1')]:
        placements.append(placement('prince-01/'+slot,ref,torso))
    placements.extend([placement('prince-01/head','aurelian.head@12',head),placement('prince-01/helmet','aurelian.dragon-prince-helmet@6',head),
        placement('prince-01/lance','aurelian.dragon-prince-lance@1',multiply(translation([1.5,-1,10.4]),rotation('x',15))),
        placement('prince-01/shield','aurelian.dragon-prince-shield@6',multiply(translation([-1.5,-1,10.4]),multiply(rotation('z',-40),translation([0,-.5,0]))))])
    (ROOT/'specs/elf-dragon-prince.json').write_text(json.dumps(dict(schema_version=1,assembly_id='aurelian-dragon-prince',label='Dragon Prince cavalry',placements=placements),indent=2)+'\n')
    (ROOT/'tests/fixtures/dragon-prince-v1-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n')
    (ROOT/'tests/fixtures/dragon-prince-barding-v2-golden.json').write_text(json.dumps({bard.reference:bard.sha256},indent=2)+'\n')
    (ROOT/'tests/fixtures/dragon-prince-reference-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in reference},indent=2)+'\n')

if __name__=='__main__':main()
