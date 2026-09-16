"""Local model review, deterministic row planning and persistent export jobs."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import threading
import uuid
import os
from functools import lru_cache

from .army import load_model
from .components.parts import catalog
from .components.elves_v2 import multiply, translation

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT/'out/viewer'
JOBS = ROOT/'out/workshop-jobs'
LOCK = threading.Lock()
ACTIVE = None


def source_revision():
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for folder in
                 (ROOT/'specs',ROOT/'fdm_sculpt/components/parts') for p in sorted(folder.rglob('*.json')))


@lru_cache(maxsize=2)
def definitions_at(revision):
    return catalog()


@lru_cache(maxsize=100)
def resolved_model(path, revision):
    return load_model(path,definitions_at(revision))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def models():
    result = []
    for family in ('spearmen', 'archers', 'swordmasters'):
        for path in sorted((ROOT/'specs/models'/family).glob('*.json')):
            slug = path.stem
            label = slug.split('-', 1)[1].replace('-', ' ').capitalize()
            result.append(dict(id=family+'/'+slug, family=family, label=label,
                               command='sergeant' in slug, path=str(path)))
    for family, name, label in [('spearmen','elf-standard-bearer','Standard bearer'),
                                ('archers','elf-archer-sergeant','Horn sergeant'),
                                ('swordmasters','elf-swordmaster-sergeant','Sergeant')]:
        result.append(dict(id=family+'/'+name, family=family, label=label, command=True,
                           path=str(ROOT/'specs/models'/f'{name}.json')))
    return result


def public_models():
    return [{k:v for k,v in m.items() if k != 'path'} for m in models()]


def choose(request, entries=None):
    entries = models() if entries is None else entries
    by_id = {m['id']:m for m in entries}
    seed = request.get('seed')
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise ValueError('Seed must be an integer from 0 to 2147483647')
    family = request.get('family')
    if family not in ('spearmen','archers','swordmasters'):
        raise ValueError('Choose an infantry unit type')
    unique = request.get('unique', False)
    maximum = request.get('max_command', 1)
    if type(unique) is not bool or type(maximum) is not int or not 0 <= maximum <= 5:
        raise ValueError('Invalid duplicate or command constraint')
    if request.get('mode', 'manual') == 'random':
        pool = request.get('pool')
        if not isinstance(pool, list) or not pool or len(pool)>100 or any(not isinstance(i,str) for i in pool) or len(pool) != len(set(pool)):
            raise ValueError('Select a nonempty pool of different variants')
        if any(not isinstance(i,str) or i not in by_id or by_id[i]['family'] != family for i in pool):
            raise ValueError('The variant pool must belong to the chosen unit type')
        rng = random.Random(seed)
        slots = []
        # Backtracking avoids greedy dead ends when the pool has few regulars.
        def fill():
            if len(slots) == 5:
                return True
            candidates = sorted(pool)
            rng.shuffle(candidates)
            for item in candidates:
                if unique and item in slots:
                    continue
                if by_id[item]['command'] and sum(by_id[i]['command'] for i in slots) >= maximum:
                    continue
                slots.append(item)
                if fill():
                    return True
                slots.pop()
            return False
        if not fill():
            raise ValueError('The pool cannot fill five slots with these constraints')
    elif request.get('mode', 'manual') == 'manual':
        slots = request.get('slots')
    else:
        raise ValueError('Unknown row selection mode')
    if not isinstance(slots,list) or len(slots) != 5 or any(not isinstance(i,str) or i not in by_id for i in slots):
        raise ValueError('Choose a known model for each of the five slots')
    if any(by_id[i]['family'] != family for i in slots):
        raise ValueError('All row models must belong to the selected unit type')
    if unique and len(set(slots)) != 5:
        raise ValueError('Repeated variants are disabled')
    if sum(by_id[i]['command'] for i in slots) > maximum:
        raise ValueError('This row exceeds the command-model limit')
    return slots


def assets_for(assembly):
    available = {}
    for path in sorted((DATA/'reviews').glob('*.json')):
        for ref, asset in json.loads(path.read_text())['assets'].items():
            key = ref,asset['definition_sha256']
            # Older saved reviews lack exact-piece ranges. Do not let one
            # replace a newer export for the same immutable component.
            if key not in available or asset.get('pieces') or not available[key].get('pieces'):
                available[key] = asset
    result = {}
    for p in assembly['placements']:
        key = p['part'], p['definition_sha256']
        if key not in available:
            raise ValueError('Model needs a cached visual review for '+p['part'])
        result[p['part']] = available[key]
    return result


def manifest(assembly, seed=1001):
    value = dict(assembly=assembly, assets=assets_for(assembly), seed=seed,
                 build=assembly.get('label',assembly['assembly_id']), visual_only=True)
    value['revision'] = digest(value)
    value['updated'] = datetime.now(timezone.utc).isoformat()
    return value


def model_review(model_id):
    entry = next((m for m in models() if m['id'] == model_id), None)
    if entry is None:
        raise ValueError('Unknown model')
    assembly = deepcopy(resolved_model(entry['path'],source_revision()))
    for p in assembly['placements']:
        p['instance_id'] = 'model/'+p['instance_id']
    assembly['label'] = entry['label']
    return manifest(assembly)


def plan(request):
    slots = choose(request)
    revision = source_revision()
    by_id = {m['id']:m for m in models()}
    # Reuse the reviewed strip and terrain. Geometry is never scaled to fit.
    source = json.loads((ROOT/'specs/elf-modular-visual.json').read_text())
    placements = deepcopy([p for p in source['placements'] if '/' not in p['instance_id']])
    for index, model_id in enumerate(slots):
        model = resolved_model(by_id[model_id]['path'], revision)
        mount = translation([-8+4*index,0,1])
        for p in model['placements']:
            placements.append(dict(p, instance_id=f'row-{index+1:02}/'+p['instance_id'],
                                   mount=multiply(mount,p['mount'])))
    assembly = dict(schema_version=1, assembly_id='workshop-row', label='Custom infantry row', placements=placements)
    pinned = dict(assembly=assembly, seed=request['seed'], slots=slots,
                  constraints=dict(family=request['family'], unique=request.get('unique',False),
                                   max_command=request.get('max_command',1)),
                  base_mm=[20,5,2], spacing_mm=4)
    pinned['plan_sha256'] = digest(pinned)
    return pinned


def job_status(job_id):
    if not isinstance(job_id,str) or len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Invalid job ID')
    path = JOBS/job_id/'status.json'
    if not path.exists():
        raise ValueError('Unknown export job')
    result = json.loads(path.read_text())
    process_path=path.parent/'process.json'
    if process_path.exists():
        result['pid']=json.loads(process_path.read_text())['pid']
    if result['state'] in ('running','queued') and result.get('pid') and not process_running(result['pid']):
        result.update(state='failed',message='The export process stopped before completion. Its files were preserved; start a new export to retry.')
        write(path,result)
    return result


def process_running(pid):
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x100000,False,pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle,0) == 0x102
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:
        return False


def jobs():
    return [job_status(p.parent.name) for p in sorted(JOBS.glob('*/status.json'),
                                                    key=lambda p:p.stat().st_mtime,reverse=True)][:20]


def start_export(request):
    global ACTIVE
    pinned = plan(request)
    if request.get('plan_sha256') != pinned['plan_sha256']:
        raise ValueError('Preview this exact row before exporting; its model revisions may have changed')
    with LOCK:
        if ACTIVE is not None and ACTIVE.poll() is None:
            raise ValueError('An export is already running. Wait for it to finish before starting another')
        if any(j['state'] in ('queued','running') and j.get('pid') and process_running(j['pid']) for j in jobs()):
            raise ValueError('An export is already running. Wait for it to finish before starting another')
        job_id = uuid.uuid4().hex
        directory = JOBS/job_id
        write(directory/'plan.json',pinned)
        write(directory/'status.json',dict(id=job_id,state='queued',message='Waiting to compose cached parts',
                                          plan_sha256=pinned['plan_sha256']))
        try:
            with (directory/'worker.log').open('w') as log:
                ACTIVE = subprocess.Popen([sys.executable,'-m','fdm_sculpt.workshop_worker',job_id],
                                          cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                                          start_new_session=os.name != 'nt',
                                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                write(directory/'process.json',dict(pid=ACTIVE.pid))
        except OSError as exc:
            write(directory/'status.json',dict(id=job_id,state='failed',message='Could not start export: '+str(exc)))
            raise
        return job_status(job_id)


def feedback(request):
    note = request.get('note')
    if not isinstance(note,str) or not note.strip() or len(note)>8000:
        raise ValueError('Enter feedback (up to 8000 characters)')
    # Store only JSON context, never execute or interpret feedback as code.
    record = {key:request.get(key) for key in ('note','model','revision','component','camera','target')}
    record['created'] = datetime.now(timezone.utc).isoformat()
    feedback_id = uuid.uuid4().hex
    write(ROOT/'out/sculpt-feedback'/f'{feedback_id}.json',record)
    return dict(id=feedback_id,message='Feedback saved with model revision and viewing angle')


def cancel_export(job_id):
    with LOCK:
        status=job_status(job_id)
        if status['state'] not in ('queued','running'):
            raise ValueError('This export is no longer running')
        pid=status.get('pid')
        if not pid:
            raise ValueError('The export is still starting; try again shortly')
        if process_running(pid):
            if os.name == 'nt':
                subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],check=True,capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
            else:
                import signal
                os.killpg(pid,signal.SIGTERM)
        status.update(state='cancelled',message='Export cancelled. The selected row and build evidence were preserved.')
        write(JOBS/job_id/'status.json',status)
        return status
