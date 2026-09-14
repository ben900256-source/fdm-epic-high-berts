import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const $ = id => document.getElementById(id);
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
let reviewUrls=new Map(), reviewOptions='', pendingRefresh=false;
scene.add(model);
const geometries = new Map();
const composer=new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const hoverOutline=new OutlinePass(new THREE.Vector2(innerWidth,innerHeight),scene,camera);
hoverOutline.visibleEdgeColor.set('#ff8c20');
hoverOutline.hiddenEdgeColor.set('#000000');
hoverOutline.edgeStrength=4;
hoverOutline.edgeThickness=2;
composer.addPass(hoverOutline);
composer.addPass(new OutputPass());
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let ctrlHeld=false,pointerOverModel=false,pointerX=0,pointerY=0;
function clearHover(){
  hoverOutline.selectedObjects=[];
  $('piece-label').hidden=true;
  delete document.body.dataset.hoveredPiece;
}
function pickPiece(){
  if(!ctrlHeld||!pointerOverModel){clearHover();return;}
  const bounds=renderer.domElement.getBoundingClientRect();
  pointer.set((pointerX-bounds.left)/bounds.width*2-1,-(pointerY-bounds.top)/bounds.height*2+1);
  scene.updateMatrixWorld();camera.updateMatrixWorld();
  raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObjects(model.children.filter(mesh=>mesh.visible),false)[0];
  if(!hit){clearHover();return;}
  const mesh=hit.object,p=mesh.userData;
  hoverOutline.selectedObjects=[mesh];
  const [figure,part]=p.instance_id.split('/');
  const name=displayName((part||figure).replaceAll('-',' '));
  const figureName=displayName(figure.charAt(0).toUpperCase()+figure.slice(1).replaceAll('-',' '));
  $('piece-name').textContent=name.charAt(0).toUpperCase()+name.slice(1)+(part?' · '+figureName:'');
  $('piece-reference').textContent=p.part;
  const label=$('piece-label');label.hidden=false;
  label.style.left=Math.max(8,Math.min(pointerX+16,innerWidth-label.offsetWidth-12))+'px';
  label.style.top=Math.max(8,Math.min(pointerY+16,innerHeight-label.offsetHeight-12))+'px';
  document.body.dataset.hoveredPiece=p.instance_id;
}
renderer.domElement.addEventListener('pointermove',event=>{
  pointerX=event.clientX;pointerY=event.clientY;pointerOverModel=true;ctrlHeld=event.ctrlKey;pickPiece();
});
renderer.domElement.addEventListener('pointerleave',()=>{pointerOverModel=false;clearHover();});
addEventListener('keydown',event=>{if(event.key==='Control'){ctrlHeld=true;pickPiece();}});
addEventListener('keyup',event=>{if(event.key==='Control'){ctrlHeld=false;clearHover();}});
addEventListener('blur',()=>{ctrlHeld=false;clearHover();});
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
  const data=new THREE.InterleavedBuffer(new Float32Array(buffer),6);
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.InterleavedBufferAttribute(data,3,0));
  g.setAttribute('normal',new THREE.InterleavedBufferAttribute(data,3,3));
  g.computeBoundingBox(); g.computeBoundingSphere();
  geometries.set(asset.url,g); return g;
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
    mesh.visible=($('figure').value==='all'||p.instance_id.split('/')[0]===$('figure').value)
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
    const next=await (await checkedFetch(reviewUrls.get(selected)||'/data/latest.json')).json();
    if(next.revision!==manifest?.revision) {
      $('status').textContent='Loading updated model…';
      const loaded=new Map(await Promise.all(Object.entries(next.assets).map(async([ref,a])=>[ref,await geometry(a)])));
      // A selection made during loading wins over the earlier request.
      if($('review').value!==selected) {pendingRefresh=true;return;}
      const replacement=new THREE.Group();
      for(const p of next.assembly.placements) {
        if(next.assets[p.part].definition_sha256!==p.definition_sha256) throw new Error('Component revision mismatch.');
        const mesh=new THREE.Mesh(loaded.get(p.part),material);
        const url=next.assets[p.part].url;
        if(!edgeGeometries.has(url)) edgeGeometries.set(url,new THREE.EdgesGeometry(mesh.geometry,25));
        const edges=new THREE.LineSegments(edgeGeometries.get(url),edgeMaterial);
        edges.visible=$('outlines').checked;
        mesh.add(edges);
        mesh.matrixAutoUpdate=false; mesh.matrix.set(...p.mount.flat()); mesh.userData=p;
        replacement.add(mesh);
      }
      const first=!manifest, changedAssembly=manifest?.assembly.assembly_id!==next.assembly.assembly_id;
      clearHover();scene.remove(model); model=replacement; scene.add(model); manifest=next;
      if(changedAssembly){$('figure').value='all';$('part').value='all';}
      options($('figure'),[...new Set(next.assembly.placements.filter(p=>p.instance_id.includes('/')).map(p=>p.instance_id.split('/')[0]))],'All figures');
      options($('part'),Object.keys(next.assets).sort(),'All components');
      visibility();
      if(first||changedAssembly) fit(new THREE.Vector3(.45,-1,.35).normalize());
      // Keep recently viewed pieces warm when switching between unit variants.
      const active=new Set(Object.values(next.assets).map(a=>a.url));
      for(const [url,g] of geometries) if(geometries.size>128&&!active.has(url)){
        g.dispose();geometries.delete(url);edgeGeometries.get(url)?.dispose();edgeGeometries.delete(url);
      }
      $('details').textContent=`${next.build} · Revision ${next.revision.slice(0,8)}`;
      document.body.dataset.revision=next.revision;
      document.body.dataset.assembly=next.assembly.assembly_id;
    }
    $('status').textContent='Current model loaded · '+new Date(manifest.updated).toLocaleTimeString();
    $('error').textContent='';
  } catch(error) {
    $('status').textContent=manifest?'Update unavailable · showing previous model':'Model unavailable';
    $('error').textContent=error.message;
  } finally {busy=false;if(pendingRefresh){pendingRefresh=false;refresh();}}
}
$('review').onchange=refresh;
for(const id of ['figure','part']) $(id).onchange=()=>{visibility();fit();};
$('shields').onchange=visibility;
$('wire').onchange=()=>material.wireframe=$('wire').checked;
$('outlines').onchange=()=>{for(const mesh of model.children) mesh.children[0].visible=$('outlines').checked;};
$('fit').onclick=()=>fit(); $('refresh').onclick=refresh;
for(const button of document.querySelectorAll('[data-view]')) button.onclick=()=>fit(new THREE.Vector3(...({front:[0,-1,0],side:[1,0,0],back:[0,1,0]}[button.dataset.view])));
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);clearHover();});
renderer.setAnimationLoop(()=>{controls.update();if(hoverOutline.selectedObjects.length) composer.render();else renderer.render(scene,camera);});
refresh();setInterval(refresh,2000);
