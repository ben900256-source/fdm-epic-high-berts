import {test,expect} from '@playwright/test';

test.use({channel:'chrome',viewport:{width:1440,height:1000}});
test.setTimeout(90000);

test('current terrain reviews load and retain body/surface identification',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('#status')).toContainText('Current model loaded');
  const index=await(await page.request.get('http://127.0.0.1:8765/data/reviews.json')).json();
  let checked=0;
  for(const entry of index.reviews){
    const manifest=await(await page.request.get('http://127.0.0.1:8765'+entry.url)).json();
    if(!['-terrain-v3','-natural-ground-v1','-visible-soil-v1','-fitted-bow-grips-v1','-aligned-horn-hand-v1','-longer-swords-v1'].some(suffix=>manifest.build.endsWith(suffix))&&entry.id!=='aurelian-terrain-gallery')continue;
    await page.selectOption('#review',entry.id);
    await expect(page.locator('body')).toHaveAttribute('data-assembly',entry.id);
    await expect(page.locator('body')).toHaveAttribute('data-revision',entry.revision);
    expect(manifest.visual_only).toBe(true);
    expect(manifest.assembly.placements.some(p=>p.part.startsWith('aurelian.base-body-'))).toBe(true);
    checked++;
  }
  expect(checked).toBe(8);
  await page.selectOption('#review','aurelian-terrain-gallery');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-terrain-gallery');
  for(const ref of ['aurelian.base-body-4x5@1','aurelian.terrain-soil-gallery@4']){
    await page.selectOption('#part',ref);await page.click('#fit');await page.waitForTimeout(350);
    await page.keyboard.down('Control');
    let found=false;
    for(let y=250;y<850&&!found;y+=40)for(let x=400;x<1300&&!found;x+=40){
      await page.mouse.move(x,y);await page.waitForTimeout(20);
      found=!!await page.locator('body').getAttribute('data-hovered-piece');
    }
    expect(found).toBe(true);
    await expect(page.locator('#piece-reference')).toHaveText(ref);
    await page.keyboard.up('Control');
  }
  expect(errors).toEqual([]);
});
