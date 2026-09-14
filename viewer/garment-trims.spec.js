import {test,expect} from '@playwright/test';
test.use({channel:'chrome',viewport:{width:1440,height:1000}});
test.setTimeout(90000);

test('army garment trims load with matching poses and remain identifiable',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('#status')).toContainText('Current model loaded');
  const index=await(await page.request.get('http://127.0.0.1:8765/data/reviews.json')).json();
  let checked=0;
  for(const entry of index.reviews){
    const manifest=await(await page.request.get('http://127.0.0.1:8765'+entry.url)).json();
    if(!manifest.build.startsWith('elf-')||(!manifest.build.endsWith('-trim-contact-v6')&&manifest.build!=='elf-archer-variants-elevated-v1'))continue;
    const slots=new Map(manifest.assembly.placements.map(p=>[p.instance_id,p]));
    if(entry.id.includes('archer'))expect([...slots.values()].some(p=>p.part.includes('tunic-trim'))).toBe(false);
    for(const p of slots.values()){
      if(!['aurelian.skirt@3'].includes(p.part))continue;
      expect(slots.get(p.instance_id+'-trim').mount).toEqual(p.mount);
    }
    await page.selectOption('#review',entry.id);
    await expect(page.locator('body')).toHaveAttribute('data-revision',entry.revision);
    checked++;
  }
  expect(checked).toBe(9);
  for(const [id,ref] of [['aurelian-spearman-hawk-sergeant','aurelian.mail-skirt-trim-c@6']]){
    await page.selectOption('#review',id);
    await expect(page.locator('body')).toHaveAttribute('data-assembly',id);
    await page.selectOption('#part',ref);await page.click('#fit');await page.waitForTimeout(300);
    await page.keyboard.down('Control');
    let found=false;
    for(let y=250;y<850&&!found;y+=40)for(let x=400;x<1300&&!found;x+=40){
      await page.mouse.move(x,y);await page.waitForTimeout(15);
      found=!!await page.locator('body').getAttribute('data-hovered-piece');
    }
    expect(found).toBe(true);
    await expect(page.locator('#piece-reference')).toHaveText(ref);
    await page.keyboard.up('Control');
    await page.selectOption('#part','all');
  }
  expect(errors).toEqual([]);
});
