import {test,expect as baseExpect} from '@playwright/test';
const expect=baseExpect.configure({timeout:60000});
test.use({channel:'chrome',viewport:{width:1600,height:1100}});
test.setTimeout(120000);

test('individual review, constrained row planning and safe preview invalidation',async({page})=>{
  // Fixed fresh seeds keep the randomize regression deterministic.
  await page.addInitScript(()=>{
    const original=crypto.getRandomValues.bind(crypto);let seed=1002;
    crypto.getRandomValues=array=>{
      if(array instanceof Uint32Array&&array.length===1){array[0]=seed++;return array;}
      return original(array);
    };
  });
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  await expect(page.locator('#row-unique')).not.toBeChecked();
  await page.click('#tab-row');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','workshop-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  await page.selectOption('#slot-1','spearmen/01-standing-guard');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('body')).toHaveAttribute('data-assembly','workshop-row');
  await page.locator('#row-tools details').evaluate(el=>el.open=true);
  await page.check('#row-unique');
  await expect(page.locator('#export-row')).toBeDisabled();
  await page.click('#preview-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('#workshop-error')).toBeEmpty();
  // Manual slot edits ignore both limits without changing randomization settings.
  await page.selectOption('#slot-2','spearmen/elf-spearman-sword-sergeant');
  await expect(page.locator('#export-row')).toBeEnabled();
  await page.selectOption('#slot-3','spearmen/elf-spearman-sword-sergeant');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('#workshop-error')).toBeEmpty();
  await expect(page.locator('#row-unique')).toBeChecked();
  await expect(page.locator('#row-command')).toHaveValue('1');
  await page.click('#random-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  const first=await page.locator('.row-slot select').evaluateAll(items=>items.map(i=>i.value));
  expect(new Set(first).size).toBe(5);
  expect(first.filter(id=>/sergeant|bearer/.test(id)).length).toBeLessThanOrEqual(1);
  await expect(page.locator('#row-seed')).toHaveValue('1002');
  await page.click('#random-row');
  await expect(page.locator('#row-status')).toContainText('preview ready');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('#row-seed')).toHaveValue('1003');
  const second=await page.locator('.row-slot select').evaluateAll(items=>items.map(i=>i.value));
  expect(second).not.toEqual(first);
  expect(new Set(second).size).toBe(5);
  // A plain preview keeps that selection and seed for the eventual export.
  await page.click('#preview-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  expect(await page.locator('.row-slot select').evaluateAll(items=>items.map(i=>i.value))).toEqual(second);
  await expect(page.locator('#row-seed')).toHaveValue('1003');
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

test('slot changes preview automatically and the latest selection wins',async({page})=>{
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  const initialResponse=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan'));
  await page.click('#tab-row');
  const initial=await (await initialResponse).json();
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('#row-slots button')).toHaveCount(0);
  let releaseFirst,firstArrived;
  const gate=new Promise(resolve=>releaseFirst=resolve);
  const arrived=new Promise(resolve=>firstArrived=resolve);
  await page.route('**/api/rows/plan',async route=>{
    if(route.request().postDataJSON().slots[0]==='spearmen/07-sword-low'){
      const response=await route.fetch();firstArrived();await gate;
      await route.fulfill({response});
    }else await route.continue();
  });
  await page.selectOption('#slot-0','spearmen/07-sword-low');
  await arrived;
  await expect(page.locator('#export-row')).toBeDisabled();
  const latestResponse=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan')&&r.request().postDataJSON().slots[0]==='spearmen/08-sword-guard');
  await page.selectOption('#slot-0','spearmen/08-sword-guard');
  const latest=await (await latestResponse).json();
  await expect(page.locator('body')).toHaveAttribute('data-revision',latest.review.revision);
  await expect(page.locator('#export-row')).toBeEnabled();
  const unchanged=review=>review.assembly.placements.filter(p=>!p.instance_id.startsWith('row-01/'));
  expect(unchanged(latest.review)).toEqual(unchanged(initial.review));
  const oldResponse=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan')&&r.request().postDataJSON().slots[0]==='spearmen/07-sword-low');
  releaseFirst();await oldResponse;
  await expect(page.locator('#activity-progress')).toBeHidden();
  await expect(page.locator('body')).toHaveAttribute('data-revision',latest.review.revision);
  await expect(page.locator('#slot-0')).toHaveValue('spearmen/08-sword-guard');
  await expect(page.locator('#workshop-error')).toBeEmpty();
  await page.route('**/api/rows/export',route=>{
    const body=route.request().postDataJSON();
    expect(body.slots[0]).toBe('spearmen/08-sword-guard');
    expect(body.plan_sha256).toBe(latest.plan.plan_sha256);
    return route.fulfill({status:400,json:{error:'Export selection checked'}});
  });
  await page.click('#export-row');
  await expect(page.locator('#workshop-error')).toContainText('Export selection checked');
});

test('local API rejects remote origins and unpreviewed exports',async({request})=>{
  const catalog=await (await request.get('http://127.0.0.1:8765/api/catalog')).json();
  const body={family:'spearmen',seed:1001,slots:Array(5).fill('spearmen/01-standing-guard')};
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body})).status()).toBe(403);
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body,headers:{'X-Workshop-Token':catalog.token,Origin:'https://unrelated.example'}})).status()).toBe(403);
  expect((await request.post('http://127.0.0.1:8765/api/rows/export',{data:body,headers:{'X-Workshop-Token':catalog.token}})).status()).toBe(400);
});

test('magnet holes default off, update the preview, and travel with the export',async({page})=>{
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  await page.click('#tab-row');
  await expect(page.locator('#row-magnets')).not.toBeChecked();
  await expect(page.locator('#export-row')).toBeEnabled();
  const plainResponse=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan'));
  await page.click('#preview-row');
  const plain=await (await plainResponse).json();
  await expect(page.locator('#export-row')).toBeEnabled();
  expect(plain.plan.magnet_holes).toBe(false);
  expect(plain.plan.assembly.placements.find(p=>p.instance_id==='strip').part).toBe('aurelian.base-body-20x5-plain@1');
  await page.check('#row-magnets');
  await expect(page.locator('#export-row')).toBeDisabled();
  const magnetResponse=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan'));
  await page.click('#preview-row');
  const magnets=await (await magnetResponse).json();
  await expect(page.locator('#export-row')).toBeEnabled();
  expect(magnets.plan.magnet_holes).toBe(true);
  expect(magnets.plan.plan_sha256).not.toBe(plain.plan.plan_sha256);
  expect(magnets.plan.assembly.placements.find(p=>p.instance_id==='strip').part).toBe('aurelian.base-body-20x5@1');
  await page.route('**/api/rows/export',route=>{
    const body=route.request().postDataJSON();
    expect(body.magnet_holes).toBe(true);
    expect(body.plan_sha256).toBe(magnets.plan.plan_sha256);
    return route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Export request captured'})});
  });
  await page.click('#export-row');
  await expect(page.locator('#workshop-error')).toContainText('Export request captured');
  await page.uncheck('#row-magnets');
  await expect(page.locator('#export-row')).toBeDisabled();
});

test('row tab previews immediately with planning and part-loading progress',async({page})=>{
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  let releasePlan,releaseParts;
  const planGate=new Promise(resolve=>releasePlan=resolve);
  const partGate=new Promise(resolve=>releaseParts=resolve);
  await page.route('**/api/rows/plan',async route=>{await planGate;await route.continue();});
  await page.route('**/*.bin',async route=>{await partGate;await route.continue();});
  await page.click('#tab-row');
  await expect(page.locator('#activity-label')).toHaveText('Preparing five-figure row…');
  await expect(page.locator('#activity-progress progress')).not.toHaveAttribute('value');
  releasePlan();
  await expect(page.locator('#activity-label')).toContainText('Loading parts');
  await expect(page.locator('#activity-progress progress')).toHaveAttribute('max',/^[1-9]\d*$/);
  await page.screenshot({path:'../out/row-loading-progress.png'});
  releaseParts();
  await expect(page.locator('body')).toHaveAttribute('data-assembly','workshop-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  await expect(page.locator('#activity-progress')).toBeHidden();
  await page.screenshot({path:'../out/row-ready.png'});
  await page.selectOption('#figure','row-01');
  await page.click('#tab-row');
  await expect(page.locator('#figure')).toHaveValue('all');
  await expect(page.locator('#part')).toHaveValue('all');
  // Changing family while in row mode also renders its default five figures.
  const changed=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan'));
  await page.selectOption('#unit-family','archers');
  const result=await (await changed).json();
  expect(result.plan.constraints.family).toBe('archers');
  await expect(page.locator('body')).toHaveAttribute('data-revision',result.review.revision);
  await expect(page.locator('#export-row')).toBeEnabled();
});

test('late row failures cannot replace a newer model view or leave progress stuck',async({page})=>{
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  let release;
  const gate=new Promise(resolve=>release=resolve);
  await page.route('**/api/rows/plan',async route=>{
    await gate;
    await route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Old row request failed'})});
  });
  await page.click('#tab-row');
  await expect(page.locator('#activity-label')).toContainText('Preparing five-figure row');
  await page.click('#tab-model');
  const response=page.waitForResponse(r=>r.url().endsWith('/api/rows/plan'));
  release();await response;
  await expect(page.locator('#activity-progress')).toBeHidden();
  await expect(page.locator('#workshop-error')).toBeEmpty();
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  await page.click('#tab-row');
  await expect(page.locator('#workshop-error')).toContainText('Old row request failed');
  await expect(page.locator('#activity-progress')).toBeHidden();
  await expect(page.locator('#export-row')).toBeDisabled();
});

test('background export cards show progress and finish cleanly',async({page})=>{
  let jobs=[];
  await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
  await page.route('**/api/rows/export',route=>{
    jobs=[{id:'12345678901234567890123456789012',state:'running',message:'Combining the row and writing STL…'}];
    return route.fulfill({json:jobs[0]});
  });
  await page.goto('http://127.0.0.1:8765');
  await expect(page.locator('body')).toHaveAttribute('data-assembly','aurelian-spearman-standing-guard');
  await page.click('#tab-row');
  await expect(page.locator('#export-row')).toBeEnabled();
  await page.click('#export-row');
  const card=page.locator('#job-list .job');
  await expect(card.locator('progress')).toBeVisible();
  await expect(card.locator('progress')).not.toHaveAttribute('value');
  await expect(card).toContainText('Combining the row and writing STL');
  jobs=[{...jobs[0],state:'complete',message:'STL generated by Blender. Unchecked output.'}];
  await expect(card).toContainText('complete');
  await expect(card.locator('progress')).toHaveCount(0);
});
