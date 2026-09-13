import {test,expect} from '@playwright/test';

test.use({channel:'chrome',viewport:{width:1440,height:1000}});
test.setTimeout(90000);

test('ten spearmen, hawk sergeant and aligned horn hand load their current revisions',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('#status')).toContainText('Current model loaded');
  const index=await(await page.request.get('http://127.0.0.1:8765/data/reviews.json')).json();
  for(const [id,build] of [
    ['aurelian-spearman-variants','elf-spearman-variants-forward-swords-v2'],
    ['aurelian-spearman-hawk-sergeant','elf-spearman-hawk-sergeant-forward-swords-v2'],
    ['aurelian-archer-sergeant','elf-archer-sergeant-aligned-horn-hand-v1']]){
    const entry=index.reviews.find(e=>e.id===id);
    expect(entry).toBeTruthy();
    const manifest=await(await page.request.get('http://127.0.0.1:8765'+entry.url)).json();
    expect(manifest.build).toBe(build);
    expect(manifest.visual_only).toBe(true);
    await page.selectOption('#review',id);
    await expect(page.locator('body')).toHaveAttribute('data-revision',entry.revision);
    if(id==='aurelian-spearman-variants'){
      await expect(page.locator('#figure option[value^="variant-"]')).toHaveCount(10);
      expect(manifest.assembly.placements.filter(p=>p.part==='aurelian.shortblade@2')).toHaveLength(4);
    }
    const ref=id==='aurelian-archer-sergeant'?'aurelian.archer-signal-horn-arm@2':'aurelian.hunting-hawk@2';
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
