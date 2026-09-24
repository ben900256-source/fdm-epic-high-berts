import {beginProgress} from './progress.js';

export async function initWorkshop({showReview,showSavedReview,initialReview,context}){
  const panel=document.createElement('section');panel.id='workshop';
  panel.innerHTML=`
    <nav class="tabs"><button id="tab-model" aria-pressed="true">Model review</button><button id="tab-row" aria-pressed="false">Build a row</button><button id="tab-trials" aria-pressed="false">Saved reviews</button></nav>
    <div id="trial-tools" hidden><label for="trial-review">Current review</label><select id="trial-review"></select><p class="hint">Current units and reusable parts. The locked spearmen are the default.</p></div>
    <label for="unit-family">Unit type</label><select id="unit-family"><option value="spearmen">Spearmen</option><option value="swordsmen">Swordsmen</option><option value="archers">Archers</option><option value="swordmasters">Bertmasters</option></select>
    <div id="model-tools"><label for="single-model">Individual model</label><select id="single-model"></select>
    <details id="feedback-tools"><summary>Sculpting feedback</summary><p class="hint">Choose a component below to focus your feedback. The model revision and viewing angle are saved with your note.</p><label for="feedback-note">What would you like changed?</label><textarea id="feedback-note" rows="3" maxlength="8000"></textarea><button id="save-feedback">Save feedback</button><p id="feedback-status" role="status"></p></details></div>
    <div id="row-tools" hidden><p class="hint">Five infantry · 20 × 5 × 1 mm base · 0.5 mm terrain texture · 4 mm spacing.</p>
    <label class="check"><input id="row-magnets" type="checkbox">Magnet holes (3 × 1 mm magnets; 2 mm base)</label>
    <p class="hint">Optional: two underside pockets, 3.2 mm diameter × 1.1 mm deep.</p>
    <div id="row-slots"></div><details><summary>Randomization constraints &amp; pool</summary>
    <p class="hint">These limits apply to Randomize row. Manual slot choices override them.</p>
    <label for="row-seed">Seed</label><input id="row-seed" type="number" min="0" max="2147483647" step="1" value="1001">
    <label class="check"><input id="row-unique" type="checkbox">No repeated variants</label>
    <label for="row-command">Maximum command models</label><input id="row-command" type="number" min="0" max="5" step="1" value="1">
    <p class="hint">Allowed variants for random selection</p><div id="variant-pool"></div></details>
    <div class="views"><button id="random-row">Randomize row</button><button id="preview-row">Preview row</button></div>
    <button id="export-row" class="primary" disabled>Generate STL</button>
    <p class="hint">Blender Boolean Union → STL. Unchecked output; no validation or slicing.</p>
    <p id="row-status" role="status"></p></div>
    <p id="workshop-error" role="alert"></p>`;
  document.querySelector('aside').prepend(panel);
  const saved=document.createElement('details');saved.id='saved-reviews';
  saved.innerHTML='<summary>Saved unit / part reviews</summary>';
  const review=document.getElementById('review');
  const label=document.querySelector('label[for="review"]');
  panel.after(saved);saved.append(label,review);
  const jobsPanel=document.createElement('section');jobsPanel.id='export-jobs';
  jobsPanel.innerHTML='<h2>STL exports</h2><p class="hint">Your row exports appear here.</p><div id="job-list"></div>';
  document.body.append(jobsPanel);
  const $=id=>document.getElementById(id);
  let token,entries=[],pinned=null,reviewSequence=0,planSequence=0,reviewActivity;
  function reviewing(label){reviewActivity?.finish();return reviewActivity=beginProgress(label);}
  async function api(path,body){
    const response=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Workshop-Token':token},body:JSON.stringify(body)});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'Workshop request failed');return result;
  }
  function guard(action){return async()=>{try{$('workshop-error').textContent='';await action();}catch(e){$('workshop-error').textContent=e.message;}};}
  function invalidate(){pinned=null;$('export-row').disabled=true;$('row-status').textContent='Preview the row after changing its selection or constraints.';}
  function familyModels(){return entries.filter(m=>m.family===$('unit-family').value);}
  function fillSelect(select,selected){select.replaceChildren(...familyModels().map(m=>new Option(m.label+(m.command?' · command':''),m.id)));if(selected)select.value=selected;}
  function request(mode='manual'){
    return {family:$('unit-family').value,seed:Number($('row-seed').value),unique:$('row-unique').checked,
      max_command:Number($('row-command').value),magnet_holes:$('row-magnets').checked,mode,
      slots:[...document.querySelectorAll('.row-slot select')].map(s=>s.value),
      pool:[...document.querySelectorAll('#variant-pool input:checked')].map(s=>s.value)};
  }
  async function individual(){
    const sequence=++reviewSequence;
    const activity=reviewing('Preparing model preview…');
    try{
    const next=await api('model?id='+encodeURIComponent($('single-model').value));
    if(sequence===reviewSequence)await showReview(next,'/api/model?id='+encodeURIComponent($('single-model').value));
    }catch(error){if(sequence===reviewSequence)throw error;
    }finally{activity.finish();}
  }
  function populate(){
    const list=familyModels();fillSelect($('single-model'));
    $('row-slots').replaceChildren();$('variant-pool').replaceChildren();
    for(let i=0;i<5;i++){
      const row=document.createElement('div');row.className='row-slot';
      const label=document.createElement('label');label.textContent=`Slot ${i+1}`;
      const select=document.createElement('select');select.id=`slot-${i}`;label.htmlFor=select.id;
      fillSelect(select,list[i%list.length].id);select.onchange=guard(()=>preview('manual',{fit:false}));
      row.append(label,select);$('row-slots').append(row);
    }
    for(const model of list){
      const label=document.createElement('label');label.className='check';
      const input=document.createElement('input');input.type='checkbox';input.checked=true;input.value=model.id;input.onchange=invalidate;
      label.append(input,document.createTextNode(model.label));$('variant-pool').append(label);
    }
    invalidate();
  }
  async function preview(mode,{fit=true}={}){
    const sequence=++planSequence;
    const intent=++reviewSequence;
    const body=request(mode),version=JSON.stringify(body);pinned=null;$('export-row').disabled=true;$('row-status').textContent='Preparing row preview…';
    const activity=reviewing(mode==='random'?'Choosing row variants…':'Preparing five-figure row…');
    try{
    const result=await api('rows/plan',body);
    if(intent!==reviewSequence || sequence!==planSequence || JSON.stringify(request(mode))!==version)return;
    result.plan.slots.forEach((value,i)=>{$(`slot-${i}`).value=value;});
    const approved={...request(),plan_sha256:result.plan.plan_sha256};
    activity.update('Loading row preview…');
    await showReview(result.review);
    if(intent!==reviewSequence || sequence!==planSequence || JSON.stringify(request())!==JSON.stringify({...approved,plan_sha256:undefined}))return;
    if(fit){
      $('figure').value='all';$('part').value='all';
      $('figure').dispatchEvent(new Event('change'));
    }
    pinned=approved;$('export-row').disabled=false;
    $('row-status').textContent=`Row preview ready · seed ${body.seed} · ${body.magnet_holes?'2 mm base with two magnet pockets':'1 mm solid base'} · 0.5 mm terrain texture. Export uses these exact five variants.`;
    }catch(error){
      if(intent===reviewSequence&&sequence===planSequence){$('row-status').textContent='Row preview failed. Adjust the selection or try again.';throw error;}
    }finally{activity.finish();}
  }
  function tab(row,trials=false){
    $('trial-tools').hidden=!trials;
    $('unit-family').hidden=trials;document.querySelector('label[for="unit-family"]').hidden=trials;
    $('model-tools').hidden=row;$('row-tools').hidden=!row;
    if(trials){$('model-tools').hidden=true;$('row-tools').hidden=true;}
    $('tab-model').setAttribute('aria-pressed',String(!row&&!trials));$('tab-row').setAttribute('aria-pressed',String(row&&!trials));
    $('tab-trials').setAttribute('aria-pressed',String(trials));
  }
  async function trials(selected){
    const sequence=++reviewSequence;reviewActivity?.finish();tab(false,true);
    const response=await fetch('/data/reviews.json',{cache:'no-store'});
    if(!response.ok)throw new Error('Could not load saved reviews');
    const index=await response.json();
    if(sequence!==reviewSequence)return;
    const choices=[...index.reviews].sort((a,b)=>Number(b.id===index.default_review)-Number(a.id===index.default_review));
    const previous=selected||$('trial-review').value||index.default_review;
    $('trial-review').replaceChildren(...choices.map(r=>new Option(r.label,r.id)));
    if(choices.some(r=>r.id===previous))$('trial-review').value=previous;
    if(!$('trial-review').value)throw new Error('No saved reviews have been published yet');
    await showSavedReview($('trial-review').value);
  }
  $('tab-model').onclick=guard(async()=>{tab(false);await individual();});
  $('tab-row').onclick=guard(async()=>{tab(true);await preview('manual');});
  $('tab-trials').onclick=guard(()=>trials());
  $('trial-review').onchange=guard(()=>trials($('trial-review').value));
  review.addEventListener('change',()=>{++reviewSequence;reviewActivity?.finish();});
  $('single-model').onchange=guard(individual);
  $('unit-family').onchange=guard(async()=>{populate();if(!$('model-tools').hidden)await individual();else await preview('manual');});
  for(const id of ['row-seed','row-unique','row-command','row-magnets'])$(id).oninput=invalidate;
  $('random-row').onclick=guard(()=>{
    const previous=Number($('row-seed').value);
    let seed=crypto.getRandomValues(new Uint32Array(1))[0]&0x7fffffff;
    if(seed===previous)seed=(seed+1)%2147483648;
    $('row-seed').value=String(seed);
    return preview('random');
  });
  $('preview-row').onclick=guard(()=>preview('manual'));
  $('export-row').onclick=guard(async()=>{
    if(!pinned)throw new Error('Preview the row first');
    $('export-row').disabled=true;
    const activity=beginProgress('Starting STL export…');
    try{const job=await api('rows/export',pinned);$('row-status').textContent='Export started. You can continue reviewing models.';await poll();}
    finally{activity.finish();$('export-row').disabled=!pinned;}
  });
  $('save-feedback').onclick=guard(async()=>{
    const activity=beginProgress('Saving feedback…');
    try{
    const result=await api('feedback',{...context(),note:$('feedback-note').value});
    $('feedback-status').textContent=result.message;$('feedback-note').value='';
    }finally{activity.finish();}
  });
  let jobSignature='';
  async function poll(){
    const jobs=await api('jobs');const signature=JSON.stringify(jobs);if(signature===jobSignature)return;jobSignature=signature;
    $('job-list').replaceChildren();
    for(const job of jobs){
      const card=document.createElement('article');card.className='job';
      const heading=document.createElement('strong');heading.textContent=`Row ${job.id.slice(0,8)} · ${job.state}`;
      const message=document.createElement('p');message.textContent=job.message;card.append(heading,message);
      if(['queued','running'].includes(job.state)){
        message.id='job-status-'+job.id;message.setAttribute('role','status');
        const progress=document.createElement('progress');
        progress.setAttribute('aria-labelledby',message.id);card.append(progress);
        card.setAttribute('aria-busy','true');
        const cancel=document.createElement('button');cancel.textContent='Cancel export';
        cancel.onclick=guard(async()=>{await api('jobs/cancel',{id:job.id});await poll();});card.append(cancel);
      }
      if(job.download){const link=document.createElement('a');link.href=job.download.url;link.download=job.download.filename;link.textContent=job.export_mode==='unchecked-blender-manifold-union'?'Download STL':'Download trial STL';card.append(link);}
      if(job.report_url){const link=document.createElement('a');link.href=job.report_url;link.download='row-export-report.json';link.textContent='Download export report';card.append(link);}
      if(job.elapsed_seconds!==undefined){const p=document.createElement('p');p.textContent=`Export time: ${job.elapsed_seconds.toFixed(1)} seconds`;card.append(p);}
      if(job.assessment){const p=document.createElement('p');p.textContent=`Sliced support: ${job.assessment.deposited_layer_support?'pass':'FAIL'} · detail: ${job.assessment.face_details_survive?'pass':'FAIL'}`;card.append(p);}
      if(job.slice_error){const p=document.createElement('p');p.textContent='Sliced checks incomplete: '+job.slice_error;card.append(p);}
      $('job-list').append(card);
    }
  }
  const startup=beginProgress('Loading model choices…');
  $('tab-model').disabled=true;$('tab-row').disabled=true;$('tab-trials').disabled=true;
  try{
    const data=await api('catalog');token=data.token;entries=data.models;populate();
    $('tab-model').disabled=false;$('tab-row').disabled=false;$('tab-trials').disabled=false;startup.finish();
    if(initialReview||data.default_review){await trials(initialReview||data.default_review);}else{await individual();}
    await poll();
    setInterval(()=>poll().catch(e=>{$('workshop-error').textContent='Export status unavailable: '+e.message;}),3000);
  }catch(e){$('workshop-error').textContent=e.message;}finally{startup.finish();}
}
