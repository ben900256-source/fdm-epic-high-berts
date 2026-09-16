// Count real work where possible; use an indeterminate bar for server work.
const tasks=new Map();
let sequence=0,panel;

function render(){
  if(!panel){
    panel=document.createElement('section');panel.id='activity-progress';
    panel.setAttribute('aria-label','Background activity');
    panel.innerHTML='<p id="activity-label" role="status" aria-live="polite"></p><progress aria-labelledby="activity-label"></progress>';
    document.body.append(panel);
  }
  const task=[...tasks.values()].at(-1);
  panel.hidden=!task;
  if(!task)return;
  panel.querySelector('p').textContent=task.label;
  const bar=panel.querySelector('progress');
  if(task.total>0){bar.max=task.total;bar.value=task.done;}
  else bar.removeAttribute('value');
}

export function beginProgress(label){
  const id=++sequence;
  tasks.set(id,{label});render();
  return {
    update(label,done,total){if(tasks.has(id)){tasks.set(id,{label,done,total});render();}},
    finish(){tasks.delete(id);render();}
  };
}
