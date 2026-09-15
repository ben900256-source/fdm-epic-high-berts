from copy import deepcopy
import json
import pytest
from fdm_sculpt import workshop as w
from fdm_sculpt import workshop_worker as worker


def request(**changes):
    value=dict(seed=1001,family='spearmen',mode='manual',
               slots=['spearmen/01-standing-guard']*5)
    value.update(changes)
    return value


def test_defaults_allow_duplicates_and_reject_two_command_models():
    assert w.choose(request()) == request()['slots']
    with pytest.raises(ValueError,match='command-model'):
        w.choose(request(slots=['spearmen/10-hawk-sergeant']*2+request()['slots'][:3]))
    with pytest.raises(ValueError,match='Repeated'):
        w.choose(request(unique=True))


def test_random_is_deterministic_pool_limited_and_order_independent():
    pool=[m['id'] for m in w.models() if m['family']=='spearmen']
    value=request(mode='random',pool=pool,unique=True)
    first=w.choose(value)
    assert first == w.choose(dict(value,pool=list(reversed(pool))))
    assert len(set(first))==5 and set(first)<=set(pool)
    assert sum('sergeant' in m or 'bearer' in m for m in first)<=1
    assert w.choose(dict(value,seed=27))!=first
    with pytest.raises(ValueError,match='cannot fill'):
        w.choose(dict(value,pool=pool[-2:]))


@pytest.mark.parametrize('changes',[
    {'seed':True},{'seed':1.2},{'seed':-1},{'max_command':2.5},
    {'slots':['../../private']*5},{'slots':['archers/01-aiming-forward']*5},
    {'mode':'random','pool':[[1]]}, {'mode':'random','pool':[]},
])
def test_invalid_requests(changes):
    with pytest.raises(ValueError):
        w.choose(request(**changes))


def test_plan_pins_models_and_moves_whole_figures_without_geometry_changes():
    value=request()
    a=w.plan(value);b=w.plan(value)
    assert a==b
    assert a['base_mm']==[20,5,2] and a['spacing_mm']==4
    groups=[[p for p in a['assembly']['placements'] if p['instance_id'].startswith(f'row-{i:02}/')] for i in (1,2)]
    assert len(groups[0])==len(groups[1])>10
    for left,right in zip(*groups):
        assert left['part']==right['part'] and left['definition_sha256']==right['definition_sha256']
        assert right['mount'][0][3]-left['mount'][0][3]==pytest.approx(4)
        assert right['mount'][1:]==left['mount'][1:]
    assert w.plan(request(seed=2))['plan_sha256']!=a['plan_sha256']


def test_export_requires_exact_preview(monkeypatch):
    monkeypatch.setattr(w,'plan',lambda _:dict(plan_sha256='current'))
    with pytest.raises(ValueError,match='Preview this exact'):
        w.start_export(dict(plan_sha256='old'))


def test_worker_failure_exposes_report_but_no_download(tmp_path,monkeypatch):
    jobs=tmp_path/'jobs';data=tmp_path/'data';job_id='a'*32
    monkeypatch.setattr(worker,'JOBS',jobs);monkeypatch.setattr(worker,'DATA',data)
    monkeypatch.setattr(worker,'job_status',lambda _:dict(id=job_id,state='queued'))
    w.write(jobs/job_id/'plan.json',dict(assembly={},seed=1001))
    def fail(*args,**kwargs):raise RuntimeError('Blender failed to run')
    monkeypatch.setattr(worker,'blender_union',fail)
    worker.export(job_id)
    state=json.loads((jobs/job_id/'status.json').read_text())
    assert state['state']=='failed' and 'download' not in state
    assert not list(data.rglob('*.stl'))


def test_feedback_is_persisted_without_interpreting_text(tmp_path,monkeypatch):
    monkeypatch.setattr(w,'ROOT',tmp_path)
    result=w.feedback(dict(note='Keep the chainmail exactly.',revision='abc',model='guard',component='head'))
    saved=json.loads((tmp_path/'out/sculpt-feedback'/f"{result['id']}.json").read_text())
    assert saved['revision']=='abc' and saved['note']=='Keep the chainmail exactly.'


def test_worker_releases_blender_bytes_without_geometry_validation(tmp_path,monkeypatch):
    jobs=tmp_path/'jobs';data=tmp_path/'data';job_id='b'*32
    monkeypatch.setattr(worker,'JOBS',jobs);monkeypatch.setattr(worker,'DATA',data)
    monkeypatch.setattr(worker,'job_status',lambda _:dict(id=job_id,state='queued'))
    w.write(jobs/job_id/'plan.json',dict(assembly={},seed=1001,slots=['guard']*5))
    def union(pinned,directory):
        output=directory/'blender-union'
        output.mkdir()
        (output/'row.stl').write_bytes(b'Blender output, accepted without mesh validation')
        return output,dict(solver='MANIFOLD',validation_performed=False,union_seconds=.2)
    monkeypatch.setattr(worker,'blender_union',union)
    worker.export(job_id)
    state=json.loads((jobs/job_id/'status.json').read_text())
    assert state['state']=='complete' and 'Unchecked' in state['message']
    assert (data/state['download']['url'].removeprefix('/data/')).read_bytes()==b'Blender output, accepted without mesh validation'
    assert state['validation_performed'] is False
    assert not (jobs/job_id/'repeat').exists()


def test_stopped_job_is_recoverable_and_cannot_claim_download(tmp_path,monkeypatch):
    monkeypatch.setattr(w,'JOBS',tmp_path)
    monkeypatch.setattr(w,'process_running',lambda _:False)
    job_id='c'*32
    w.write(tmp_path/job_id/'status.json',dict(id=job_id,state='running',pid=99999))
    result=w.job_status(job_id)
    assert result['state']=='failed' and 'download' not in result


def test_finished_export_cannot_be_cancelled(monkeypatch):
    monkeypatch.setattr(w,'job_status',lambda _:dict(state='complete'))
    with pytest.raises(ValueError,match='no longer running'):
        w.cancel_export('d'*32)
