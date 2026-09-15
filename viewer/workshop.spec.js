import {test,expect as baseExpect} from '@playwright/test';
const expect=baseExpect.configure({timeout:60000});
test.use({channel:'chrome',viewport:{width:1600,height:1100}});
test.setTimeout(120000);

test('individual review, constrained row planning and safe preview invalidation',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  await expect(page.locator('#row-unique')).not.toBeChecked();
  await page.click('#tab-row');
  await page.selectOption('#slot-1','spearmen/01-standing-guard');
  await page.click('#preview-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('body')).toHaveAttribute('data-assembly','workshop-row');
  await page.locator('#row-tools details').evaluate(el=>el.open=true);
  await page.check('#row-unique');
  await expect(page.locator('#export-row')).toBeDisabled();
  await page.click('#preview-row');
  await expect(page.locator('#workshop-error')).toContainText('Repeated variants');
  await page.click('#random-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  const first=await page.locator('.row-slot select').evaluateAll(items=>items.map(i=>i.value));
  expect(new Set(first).size).toBe(5);
  await page.click('#random-row');
  await expect(page.locator('#row-status')).toContainText('preview ready');
  expect(await page.locator('.row-slot select').evaluateAll(items=>items.map(i=>i.value))).toEqual(first);
  await page.route('**/api/rows/export',route=>route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'An export is already running'})}));
  await page.click('#export-row');
  await expect(page.locator('#workshop-error')).toContainText('already running');
  await page.click('#tab-model');
  await page.selectOption('#unit-family','archers');
  await expect(page.locator('body')).toHaveAttribute('data-assembly',/archer/);
  await page.locator('#saved-reviews').evaluate(el=>el.open=true);
  await page.selectOption('#review','aurelian-standard-bearer');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-standard-bearer');
  await expect(page.locator('#download-stl')).toBeHidden();
  expect(errors).toEqual([]);
});

test('local API rejects remote origins and unpreviewed exports',async({request})=>{
  const catalog=await (await request.get('http://127.0.0.1:8765/api/catalog')).json();
  const body={family:'spearmen',seed:1001,slots:Array(5).fill('spearmen/01-standing-guard')};
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body})).status()).toBe(403);
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body,headers:{'X-Workshop-Token':catalog.token,Origin:'https://unrelated.example'}})).status()).toBe(403);
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body,headers:{'X-Workshop-Token':catalog.token}})).status()).toBe(400);
});
