export async function initWorkshop({showReview,context}){
  const panel=document.createElement('section');panel.id='workshop';
  panel.innerHTML=`
    <nav class="tabs"><button id="tab-model" aria-pressed="true">Model review</button><button id="tab-row" aria-pressed="false">Build a row</button></nav>
    <label for="unit-family">Unit type</label><select id="unit-family"><option value="spearmen">Spearmen</option><option value="archers">Archers</option><option value="swordmasters">Bertmasters</option></select>
    <div id="model-tools"><label for="single-model">Individual model</label><select id="single-model"></select>
    <details id="feedback-tools"><summary>Sculpting feedback</summary><p class="hint">Choose a component below to focus your feedback. The model revision and viewing angle are saved with your note.</p><label for="feedback-note">What would you like changed?</label><textarea id="feedback-note" rows="3" maxlength="8000"></textarea><button id="save-feedback">Save feedback</button><p id="feedback-status" role="status"></p></details></div>
    <div id="row-tools" hidden><p class="hint">Five infantry · 20 × 5 × 2 mm base · 4 mm spacing. Existing model shapes are preserved.</p>
    <div id="row-slots"></div><details><summary>Row constraints &amp; random pool</summary>
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
  let token,entries=[],pinned=null,reviewSequence=0,planSequence=0;
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
      max_command:Number($('row-command').value),mode,
      slots:[...document.querySelectorAll('.row-slot select')].map(s=>s.value),
      pool:[...document.querySelectorAll('#variant-pool input:checked')].map(s=>s.value)};
  }
  async function individual(){
    const sequence=++reviewSequence;
    const next=await api('model?id='+encodeURIComponent($('single-model').value));
    if(sequence===reviewSequence)await showReview(next,'/api/model?id='+encodeURIComponent($('single-model').value));
  }
  function populate(){
    const list=familyModels();fillSelect($('single-model'));
    $('row-slots').replaceChildren();$('variant-pool').replaceChildren();
    for(let i=0;i<5;i++){
      const row=document.createElement('div');row.className='row-slot';
      const label=document.createElement('label');label.textContent=`Slot ${i+1}`;
      const select=document.createElement('select');select.id=`slot-${i}`;label.htmlFor=select.id;
      fillSelect(select,list[i].id);select.onchange=invalidate;
      const back=document.createElement('button');back.textContent='↑';back.title='Swap with previous slot';back.disabled=i===0;
      back.onclick=()=>{const other=$(`slot-${i-1}`),value=select.value;select.value=other.value;other.value=value;invalidate();};
      row.append(label,select,back);$('row-slots').append(row);
    }
    for(const model of list){
      const label=document.createElement('label');label.className='check';
      const input=document.createElement('input');input.type='checkbox';input.checked=true;input.value=model.id;input.onchange=invalidate;
      label.append(input,document.createTextNode(model.label));$('variant-pool').append(label);
    }
    invalidate();
  }
  async function preview(mode){
    const sequence=++planSequence;
    const intent=++reviewSequence;
    const body=request(mode),version=JSON.stringify(body);pinned=null;$('export-row').disabled=true;$('row-status').textContent='Preparing row preview…';
    const result=await api('rows/plan',body);
    if(intent!==reviewSequence || sequence!==planSequence || JSON.stringify(request(mode))!==version)return;
    result.plan.slots.forEach((value,i)=>{$(`slot-${i}`).value=value;});
    const approved={...request(),plan_sha256:result.plan.plan_sha256};
    await showReview(result.review);
    if(intent!==reviewSequence || sequence!==planSequence || JSON.stringify(request())!==JSON.stringify({...approved,plan_sha256:undefined}))return;
    pinned=approved;$('export-row').disabled=false;
    $('row-status').textContent=`Row preview ready · seed ${body.seed}. Export uses these exact five variants.`;
  }
  function tab(row){
    $('model-tools').hidden=row;$('row-tools').hidden=!row;
    $('tab-model').setAttribute('aria-pressed',String(!row));$('tab-row').setAttribute('aria-pressed',String(row));
  }
  $('tab-model').onclick=guard(async()=>{tab(false);await individual();});
  $('tab-row').onclick=()=>{++reviewSequence;tab(true);};
  review.addEventListener('change',()=>{++reviewSequence;});
  $('single-model').onchange=guard(individual);
  $('unit-family').onchange=guard(async()=>{populate();if(!$('model-tools').hidden)await individual();});
  for(const id of ['row-seed','row-unique','row-command'])$(id).oninput=invalidate;
  $('random-row').onclick=guard(()=>preview('random'));
  $('preview-row').onclick=guard(()=>preview('manual'));
  $('export-row').onclick=guard(async()=>{
    if(!pinned)throw new Error('Preview the row first');
    $('export-row').disabled=true;
    try{const job=await api('rows/export',pinned);$('row-status').textContent='Export started. You can continue reviewing models.';await poll();}
    finally{$('export-row').disabled=!pinned;}
  });
  $('save-feedback').onclick=guard(async()=>{
    const result=await api('feedback',{...context(),note:$('feedback-note').value});
    $('feedback-status').textContent=result.message;$('feedback-note').value='';
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
  try{
    const data=await api('catalog');token=data.token;entries=data.models;populate();await individual();await poll();
    setInterval(()=>poll().catch(e=>{$('workshop-error').textContent='Export status unavailable: '+e.message;}),3000);
  }catch(e){$('workshop-error').textContent=e.message;}
}
