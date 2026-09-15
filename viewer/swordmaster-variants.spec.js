import {test,expect} from '@playwright/test';
test.use({channel:'chrome',viewport:{width:1400,height:1000}});
test('ten swordmaster variants load and their arms remain identifiable',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await page.locator('#saved-reviews').evaluate(el=>el.open=true);
  await expect(page.locator('#status')).toContainText('Current model loaded');
  await page.selectOption('#review','aurelian-swordmaster-variants');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-swordmaster-variants');
  await expect(page.locator('body')).toContainText('elf-swordmaster-variants-fitted-waist-v3');
  await expect(page.locator('#figure option[value^="variant-"]')).toHaveCount(10);
  const options=await page.locator('#figure option[value^="variant-"]').evaluateAll(nodes=>nodes.map(n=>n.value));
  for(const value of options){await page.selectOption('#figure',value);await page.click('#fit');}
  await page.selectOption('#part','aurelian.swordmaster-right-arm-pose-10@1');await page.click('#fit');
  await page.keyboard.down('Control');let found=false;
  for(let y=200;y<850&&!found;y+=50)for(let x=400;x<1250&&!found;x+=50){
    await page.mouse.move(x,y);await page.waitForTimeout(15);found=!!await page.locator('body').getAttribute('data-hovered-piece');
  }
  expect(found).toBe(true);await page.keyboard.up('Control');
  await expect(page.locator('#piece-reference')).toHaveText('aurelian.swordmaster-right-arm-pose-10@1');
  expect(errors).toEqual([]);
});
