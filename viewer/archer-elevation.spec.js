import {test,expect} from '@playwright/test';
test.use({channel:'chrome',viewport:{width:1400,height:1000}});
test('upward archer variants load in both galleries',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await page.locator('#saved-reviews').evaluate(el=>el.open=true);
  await expect(page.locator('#status')).toContainText('Current model loaded');
  for(const [id,count,build] of [['aurelian-archer-variants',13,'elf-archer-variants-elevated-v1'],['aurelian-archer-rear-ranks',3,'elf-archer-rear-ranks-v1']]){
    await page.selectOption('#review',id);
    await expect(page.locator('body')).toHaveAttribute('data-assembly',id);
    await expect(page.locator('#figure option[value^="variant-"]')).toHaveCount(count);
    await expect(page.locator('body')).toContainText(build);
  }
  await page.selectOption('#figure','variant-13-aiming-up-40');
  await page.selectOption('#part','aurelian.archer-bow-arm-elevated-40@1');await page.click('#fit');
  await page.keyboard.down('Control');let found=false;
  for(let y=200;y<850&&!found;y+=50)for(let x=400;x<1250&&!found;x+=50){
    await page.mouse.move(x,y);await page.waitForTimeout(15);
    found=!!await page.locator('body').getAttribute('data-hovered-piece');
  }
  expect(found).toBe(true);
  await expect(page.locator('#piece-reference')).toHaveText('aurelian.archer-bow-arm-elevated-40@1');
  await page.keyboard.up('Control');expect(errors).toEqual([]);
});
