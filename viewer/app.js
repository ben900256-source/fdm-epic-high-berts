import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { initWorkshop } from './workshop-ui.js';
import { beginProgress } from './progress.js';

const $ = id => document.getElementById(id);
const downloads=document.createElement('section');downloads.id='downloads';
const downloadLink=document.createElement('a');downloadLink.id='download-stl';
downloadLink.textContent='Download STL';downloadLink.hidden=true;
const downloadStatus=document.createElement('p');downloadStatus.id='download-status';
const projectLink=document.createElement('a');projectLink.id='download-project';projectLink.hidden=true;
projectLink.textContent='Download PrusaSlicer project';
downloads.append(downloadLink,projectLink,downloadStatus);document.querySelector('aside').append(downloads);
function updateDownload(review){
  const file=review.stl_download;
  const available=file && /^\/data\/downloads\/[a-f0-9]{64}\.stl$/.test(file.url);
  downloadLink.hidden=!available;
  downloadLink.style.display=available?'block':'none';
  if(available){
    downloadLink.href=file.url;downloadLink.download=file.filename;
    downloadLink.textContent=`Download STL · ${(file.bytes/1e6).toFixed(1)} MB`;
    downloadStatus.textContent=file.status;
  }else{
    downloadLink.removeAttribute('href');downloadLink.removeAttribute('download');
    downloadStatus.textContent='No print STL published for this visual review.';
  }
  const project=review.project_download;
  const projectAvailable=project&&/^\/data\/downloads\/[a-f0-9]{64}\.3mf$/.test(project.url);
  projectLink.hidden=!projectAvailable;
  if(projectAvailable){projectLink.href=project.url;projectLink.download=project.filename;}
  else{projectLink.removeAttribute('href');projectLink.removeAttribute('download');}
}
const displayName = text => text.replace(/swordmaster/gi, name => name[0]==='S'?'Bertmaster':'bertmaster');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#171e24');
const camera = new THREE.PerspectiveCamera(35,innerWidth/innerHeight,.01,2000);
camera.up.set(0,0,1);
const controls = new OrbitControls(camera,renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xe8f1ff,0x605345,2));
for (const [position,power] of [[[15,-30,40],3],[[-25,-10,15],1.5],[[5,20,25],2]]) {
  const light = new THREE.DirectionalLight(0xfff3df,power); light.position.set(...position); scene.add(light);
}
const material = new THREE.MeshStandardMaterial({color:0xc5b797,roughness:.78,metalness:.12,
  polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
const edgeMaterial = new THREE.LineBasicMaterial({color:0x302b25,transparent:true,opacity:.72});
const edgeGeometries = new Map();
let model = new THREE.Group(), manifest, busy=false;
let workshopReview=null;
let workshopSource=null;
let reviewUrls=new Map(), reviewOptions='', pendingRefresh=false;
scene.add(model);
const geometries = new Map();
const composer=new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const componentOutline=new OutlinePass(new THREE.Vector2(innerWidth,innerHeight),scene,camera);
componentOutline.visibleEdgeColor.set('#ffe033');
componentOutline.hiddenEdgeColor.set('#ffe033');
componentOutline.edgeStrength=4;
componentOutline.edgeThickness=2;
composer.addPass(componentOutline);
const hoverOutline=new OutlinePass(new THREE.Vector2(innerWidth,innerHeight),scene,camera);
hoverOutline.visibleEdgeColor.set('#ff8c20');
hoverOutline.hiddenEdgeColor.set('#ff8c20');
hoverOutline.edgeStrength=4;
hoverOutline.edgeThickness=2;
composer.addPass(hoverOutline);
composer.addPass(new OutputPass());
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let ctrlHeld=false,altHeld=false,pointerOverModel=false,pointerX=0,pointerY=0;
function clearHover(){
  componentOutline.selectedObjects=[];
  hoverOutline.selectedObjects=[];
  $('piece-label').hidden=true;
  delete document.body.dataset.hoveredPiece;
  delete document.body.dataset.hoveredRole;
  delete document.body.dataset.hoveredId;
}
function pickPiece(){
  if(!(ctrlHeld||altHeld)||!pointerOverModel){clearHover();return;}
  const bounds=renderer.domElement.getBoundingClientRect();
  pointer.set((pointerX-bounds.left)/bounds.width*2-1,-(pointerY-bounds.top)/bounds.height*2+1);
  scene.updateMatrixWorld();camera.updateMatrixWorld();
  raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObjects(model.children.filter(mesh=>mesh.visible),false)[0];
  if(!hit){clearHover();return;}
  const mesh=hit.object,p=mesh.userData;
  // Keep the exact piece orange, without blending a yellow outline into it.
  componentOutline.selectedObjects=model.children.filter(other=>other.visible&&other!==mesh&&other.userData.instance_id===p.instance_id);
  hoverOutline.selectedObjects=[mesh];
  const [figure,part]=p.instance_id.split('/');
  const readable=value=>{
    const name=displayName(value.replaceAll('_',' ').replaceAll('-',' '));
    return name.charAt(0).toUpperCase()+name.slice(1);
  };
  const componentName=readable(part||figure);
  const pieceName=p.geometry_role?readable(p.geometry_role):null;
  const figureName=displayName(figure.charAt(0).toUpperCase()+figure.slice(1).replaceAll('-',' '));
  $('piece-name').textContent=[pieceName,componentName,part?figureName:null].filter((name,index,names)=>name&&names.indexOf(name)===index).join(' · ');
  $('piece-reference').textContent=p.part;
  $('piece-id').textContent='#'+p.piece_id;
  const label=$('piece-label');label.hidden=false;
  label.style.left=Math.max(8,Math.min(pointerX+16,innerWidth-label.offsetWidth-12))+'px';
  label.style.top=Math.max(8,Math.min(pointerY+16,innerHeight-label.offsetHeight-12))+'px';
  document.body.dataset.hoveredPiece=p.instance_id;
  document.body.dataset.hoveredId=p.piece_id;
  if(p.geometry_role) document.body.dataset.hoveredRole=p.geometry_role;
  else delete document.body.dataset.hoveredRole;
}
renderer.domElement.addEventListener('pointermove',event=>{
  pointerX=event.clientX;pointerY=event.clientY;pointerOverModel=true;ctrlHeld=event.ctrlKey;altHeld=event.altKey;pickPiece();
});
renderer.domElement.addEventListener('pointerleave',()=>{pointerOverModel=false;clearHover();});
addEventListener('keydown',event=>{
  if(event.key==='Tab'&&event.altKey){altHeld=false;clearHover();return;}
  if(event.key==='Control')ctrlHeld=true;
  if(event.key==='Alt')altHeld=true;
  if(event.key==='Alt'||event.key==='Control')pickPiece();
});
addEventListener('keyup',event=>{
  if(event.key==='Control')ctrlHeld=false;
  if(event.key==='Alt')altHeld=false;
  if(event.key==='Alt'||event.key==='Control')pickPiece();
});
addEventListener('blur',()=>{ctrlHeld=false;altHeld=false;clearHover();});
controls.addEventListener('change',pickPiece);

async function checkedFetch(url) {
  const response=await fetch(url,{cache:'no-store'});
  if(!response.ok) throw new Error(`Could not load model (${response.status}).`);
  return response;
}
async function geometry(asset) {
  if(geometries.has(asset.url)) return geometries.get(asset.url);
  const buffer=await (await checkedFetch(asset.url)).arrayBuffer();
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),b=>b.toString(16).padStart(2,'0')).join('');
  if(hash!==asset.sha256 || buffer.byteLength%72) throw new Error('Model data verification failed. Previous view retained.');
  const values=new Float32Array(buffer);
  const ranges=asset.pieces||[{role:null,first_triangle:0,triangle_count:buffer.byteLength/72}];
  let end=0;
  for(const piece of ranges){
    if(!Number.isInteger(piece.first_triangle)||piece.first_triangle!==end||
       !Number.isInteger(piece.triangle_count)||piece.triangle_count<=0)
      throw new Error('Invalid model piece ranges. Previous view retained.');
    end+=piece.triangle_count;
  }
  if(end!==buffer.byteLength/72)throw new Error('Incomplete model piece ranges. Previous view retained.');
  const pieces=ranges.map((piece,index)=>{
    const data=new THREE.InterleavedBuffer(values.subarray(piece.first_triangle*18,(piece.first_triangle+piece.triangle_count)*18),6);
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.InterleavedBufferAttribute(data,3,0));
    g.setAttribute('normal',new THREE.InterleavedBufferAttribute(data,3,3));
    g.computeBoundingBox();g.computeBoundingSphere();
    return {geometry:g,role:piece.role,key:asset.url+'#'+index};
  });
  geometries.set(asset.url,pieces); return pieces;
}
function options(select, values, label) {
  const selected=select.value;
  select.replaceChildren(new Option(label,'all'),...values.map(v=>new Option(displayName(v),v)));
  select.value=values.includes(selected)?selected:'all';
}
function visibility() {
  clearHover();
  for(const mesh of model.children) {
    const p=mesh.userData;
    const slot=p.instance_id.split('/').at(-1);
    const shieldPiece=slot.includes('shield')||(slot==='part'&&p.part.includes('shield'));
    const selected=$('figure').value;
    const forwardBase=selected.startsWith('forward-')?'base-'+selected.slice('forward-'.length):null;
    mesh.visible=(selected==='all'||p.instance_id.split('/')[0]===selected
      ||(forwardBase!==null&&(p.instance_id===forwardBase||p.instance_id===forwardBase+'-terrain')))
      && ($('part').value==='all'||p.part===$('part').value)
      && ($('shields').checked||!shieldPiece);
  }
}
function fit(direction) {
  const box=new THREE.Box3();
  for(const mesh of model.children) if(mesh.visible) box.union(new THREE.Box3().setFromObject(mesh));
  if(box.isEmpty()) return;
  const center=box.getCenter(new THREE.Vector3()), size=box.getSize(new THREE.Vector3()).length();
  const vector=direction || camera.position.clone().sub(controls.target).normalize();
  if(vector.length()<.1) vector.set(.45,-1,.3).normalize();
  controls.target.copy(center);
  camera.position.copy(center).addScaledVector(vector,size/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2)))*1.25/Math.min(1,camera.aspect));
  controls.update();
}
async function refresh() {
  if(busy) {pendingRefresh=true;return;}
  busy=true;
  const selected=$('review').value;
  const requestedWorkshop=workshopReview;
  let activity;
  try {
    const index=await (await checkedFetch('/data/reviews.json')).json();
    if($('review').value!==selected){pendingRefresh=true;return;}
    reviewUrls=new Map(index.reviews.map(r=>[r.id,r.url]));
    const optionSignature=JSON.stringify(index.reviews.map(r=>[r.id,r.label]));
    if(optionSignature!==reviewOptions){
      $('review').replaceChildren(new Option('Latest update','latest'),
        ...index.reviews.map(r=>new Option(displayName(r.label),r.id)));
      $('review').value=reviewUrls.has(selected)?selected:'latest';
      reviewOptions=optionSignature;
    }
    const next=requestedWorkshop ? (workshopSource ? await (await checkedFetch(workshopSource)).json() : requestedWorkshop)
      : await (await checkedFetch(reviewUrls.get(selected)||'/data/latest.json')).json();
    if(next.revision!==manifest?.revision) {
      $('status').textContent='Loading updated model…';
      const loaded=new Map(),pending=Object.entries(next.assets);
      const total=pending.length;let completed=0;
      activity=beginProgress('Loading preview parts…');
      activity.update(`Loading parts · 0 of ${total}`,0,total);
      await Promise.all(Array.from({length:4},async()=>{
        while(pending.length){
          const [ref,asset]=pending.shift();loaded.set(ref,await geometry(asset));
          activity.update(`Loading parts · ${++completed} of ${total}`,completed,total);
        }
      }));
      // A selection made during loading wins over the earlier request.
      if($('review').value!==selected || requestedWorkshop!==workshopReview) {pendingRefresh=true;return;}
      const replacement=new THREE.Group();
      let assembled=0;
      activity.update('Drawing preview…',0,next.assembly.placements.length);
      await new Promise(requestAnimationFrame);
      for(const p of next.assembly.placements) {
        if(next.assets[p.part].definition_sha256!==p.definition_sha256) throw new Error('Component revision mismatch.');
        for(const [pieceIndex,piece] of loaded.get(p.part).entries()){
        const mesh=new THREE.Mesh(piece.geometry,material);
        if(!edgeGeometries.has(piece.key)) edgeGeometries.set(piece.key,new THREE.EdgesGeometry(mesh.geometry,25));
        const edges=new THREE.LineSegments(edgeGeometries.get(piece.key),edgeMaterial);
        edges.visible=$('outlines').checked;
        mesh.add(edges);
        const pieceId=next.piece_ids?.[p.instance_id]?.[pieceIndex];
        if(!pieceId)throw new Error('Piece IDs unavailable. Restart the viewer server.');
        mesh.matrixAutoUpdate=false; mesh.matrix.set(...p.mount.flat()); mesh.userData={...p,geometry_role:piece.role,piece_id:pieceId};
        replacement.add(mesh);
        }
        assembled++;
        activity.update(`Drawing preview · ${assembled} of ${next.assembly.placements.length} components`,assembled,next.assembly.placements.length);
        if(assembled%8===0)await new Promise(requestAnimationFrame);
      }
      if($('review').value!==selected || requestedWorkshop!==workshopReview) {pendingRefresh=true;return;}
      const first=!manifest, changedAssembly=manifest?.assembly.assembly_id!==next.assembly.assembly_id;
      clearHover();scene.remove(model); model=replacement; scene.add(model); manifest=next;
      updateDownload(next);
      if(changedAssembly){$('figure').value='all';$('part').value='all';}
      options($('figure'),[...new Set(next.assembly.placements.filter(p=>p.instance_id.includes('/')).map(p=>p.instance_id.split('/')[0]))],'All figures');
      options($('part'),Object.keys(next.assets).sort(),'All components');
      visibility();
      if(first||changedAssembly) fit(/^(flat-spear-kit|full-rounded-spear-kit)/.test(next.assembly.assembly_id)
        ?new THREE.Vector3(.1,-.35,1).normalize():new THREE.Vector3(.45,-1,.35).normalize());
      // Keep recently viewed pieces warm when switching between unit variants.
      const active=new Set(Object.values(next.assets).map(a=>a.url));
      for(const [url,pieces] of geometries) if(geometries.size>128&&!active.has(url)){
        for(const piece of pieces){piece.geometry.dispose();edgeGeometries.get(piece.key)?.dispose();edgeGeometries.delete(piece.key);}
        geometries.delete(url);
      }
      $('details').textContent=`${next.build} · Revision ${next.revision.slice(0,8)}`;
      document.body.dataset.revision=next.revision;
      document.body.dataset.assembly=next.assembly.assembly_id;
    }
    $('status').textContent='Current model loaded · '+new Date(manifest.updated).toLocaleTimeString();
    $('error').textContent='';
    return true;
  } catch(error) {
    $('status').textContent=manifest?'Update unavailable · showing previous model':'Model unavailable';
    $('error').textContent=error.message;
    return false;
  } finally {activity?.finish();busy=false;if(pendingRefresh){pendingRefresh=false;refresh();}}
}
$('review').onchange=()=>{workshopReview=null;workshopSource=null;refresh();};
for(const id of ['figure','part']) $(id).onchange=()=>{visibility();fit();};
$('shields').onchange=visibility;
$('wire').onchange=()=>material.wireframe=$('wire').checked;
$('outlines').onchange=()=>{for(const mesh of model.children) mesh.children[0].visible=$('outlines').checked;};
$('fit').onclick=()=>fit(); $('refresh').onclick=refresh;
for(const button of document.querySelectorAll('[data-view]')) button.onclick=()=>fit(new THREE.Vector3(...({front:[0,-1,0],side:[1,0,0],back:[0,1,0],top:[0,-.001,1]}[button.dataset.view])));
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);clearHover();});
renderer.setAnimationLoop(()=>{controls.update();if(hoverOutline.selectedObjects.length) composer.render();else renderer.render(scene,camera);});
initWorkshop({
  initialReview:new URL(location.href).searchParams.get('review'),
  showSavedReview:async id=>{
    workshopReview=null;workshopSource=null;
    if(![...$('review').options].some(option=>option.value===id))$('review').add(new Option(id,id));
    $('review').value=id;
    const url=new URL(location.href);url.searchParams.set('review',id);history.replaceState(null,'',url);
    if(await refresh()===false)throw new Error($('error').textContent);
  },
  showReview:async (review,source=null)=>{
    const url=new URL(location.href);url.searchParams.delete('review');history.replaceState(null,'',url);
    workshopReview=review;workshopSource=source;
    if(await refresh()===false)throw new Error($('error').textContent);
    const deadline=Date.now()+90000;
    while(manifest?.revision!==review.revision){
      if(workshopReview!==review) return;
      if(Date.now()>deadline)throw new Error('The requested preview could not be loaded.');
      await new Promise(resolve=>setTimeout(resolve,100));
    }
  },
  context:()=>({model:manifest?.assembly.assembly_id,revision:manifest?.revision,
    component:$('part').value,camera:camera.position.toArray(),target:controls.target.toArray()})
}).finally(()=>{refresh();setInterval(refresh,2000);});
