"""Keep the shaft inside the socket instead of protruding through the blade."""
from copy import deepcopy
from .spearman_overhangs import finish


def revised_spear(definitions,seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    source=definitions['aurelian.spear@4']
    data=deepcopy(source.to_dict())
    p=data['parameters']
    shaft=next(a for a in p['atoms'] if a['role']=='spear')
    shaft['end'][2]=13.20
    p['landmarks']['shaft_top'][2]=7.20
    p['landmarks']['spear'][2]=.525
    p['design'].update(shaft_length_mm=13.35,shaft_extension_mm=2.35,
        shaft_length_factor=13.35/11,
        note='Shaft ends inside the socket collar; blade outline, total height, foot and grip retained.')
    p.update(seed=seed,socket_cleanup_source=source.reference,
             socket_cleanup_source_sha256=source.sha256,
             provenance='Shorten only the hidden shaft top by 0.40 mm so the cylinder cannot break through the narrow lower blade. Socket and both blade primitives unchanged. Visual-only.')
    data.update(version=5,name='Spear with shaft seated inside the socket collar')
    return finish(data)
