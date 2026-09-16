import {test,expect} from '@playwright/test';

test.use({channel:'chrome',viewport:{width:1440,height:1000}});
test.setTimeout(90000);

test('Ctrl shows the exact piece and component together; Alt remains an alias',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('#status')).toContainText('Current model loaded');
  await page.locator('#saved-reviews').evaluate(el=>el.open=true);
  await page.selectOption('#review','aurelian-spearmen-overhang-study');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearmen-overhang-study');
  await page.selectOption('#figure','row-01');
  await page.selectOption('#part','aurelian.left-leg@5');
  await page.click('[data-view="front"]');
  await page.waitForTimeout(300);
  await page.keyboard.down('Control');
  const roles=new Set();
  for(let y=250;y<900&&roles.size<2;y+=40)for(let x=500;x<1060&&roles.size<2;x+=40){
    await page.mouse.move(x,y);
    const role=await page.locator('body').getAttribute('data-hovered-role');
    if(role){
      roles.add(role);
      await expect(page.locator('body')).toHaveAttribute('data-hovered-piece','row-01/left-leg');
      await expect(page.locator('#piece-reference')).toHaveText('aurelian.left-leg@5');
      await expect(page.locator('#piece-name')).toContainText(role.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase()));
      await expect(page.locator('#piece-name')).toContainText('Left leg');
    }
  }
  expect(roles.size).toBe(2);
  await page.screenshot({path:'../out/spearman-roomier-shoes-review/ctrl-piece-hover.png'});
  const role=await page.locator('body').getAttribute('data-hovered-role');
  await page.keyboard.down('Alt');
  await page.keyboard.up('Control');
  await expect(page.locator('#piece-name')).toContainText('Left leg');
  await expect(page.locator('#piece-reference')).toHaveText('aurelian.left-leg@5');
  await expect(page.locator('body')).toHaveAttribute('data-hovered-role',role);
  await page.keyboard.up('Alt');
  await expect(page.locator('#piece-label')).toBeHidden();
  await page.keyboard.down('Alt');
  await expect(page.locator('#piece-label')).toBeVisible();
  await page.evaluate(()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Tab',altKey:true})));
  await expect(page.locator('#piece-label')).toBeHidden();
  await page.keyboard.up('Alt');
  await page.keyboard.down('Alt');
  await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  await expect(page.locator('#piece-label')).toBeHidden();
  await page.keyboard.up('Alt');

  // Review the complete figure: the selected shoe is exposed, while its
  // component's shin and thigh sit behind the skirt and must remain outlined.
  await page.selectOption('#part','all');
  await page.locator('#shields').uncheck();
  await page.click('[data-view="front"]');
  await page.waitForTimeout(300);
  await page.keyboard.down('Control');
  let foot=false;
  for(let y=780;y<930&&!foot;y+=12)for(let x=560;x<900&&!foot;x+=12){
    await page.mouse.move(x,y);
    const picked=await page.locator('body').getAttribute('data-hovered-role');
    foot=!!picked&&/_(toe|sole)$/.test(picked);
  }
  expect(foot).toBe(true);
  await page.screenshot({path:'../out/spearman-roomier-shoes-review/occluded-component-hover.png'});
  await page.keyboard.up('Control');
  await expect(page.locator('#piece-label')).toBeHidden();
  expect(errors).toEqual([]);
});
