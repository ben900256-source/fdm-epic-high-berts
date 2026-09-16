"""Recess mail edging beneath the pointed shield using ordered Exact CSG."""
from copy import deepcopy

from .elves_v2 import identity, multiply
from .shield_tuck import inverse_rigid
from .spearman_overhangs import finish


def revised_parts(definitions, manifest, seed):
    if type(seed) is not int or seed != manifest['seed']:
        raise ValueError('seed must match the pinned trim fit manifest')
    result = []
    for pose in manifest['poses']:
        for name in ('trim', 'shield'):
            item = pose[name]
            if definitions[item['part']].sha256 != item['definition_sha256']:
                raise ValueError('pinned trim fit source changed')
        source = definitions[pose['trim']['part']]
        shield = definitions[pose['shield']['part']].to_dict()['parameters']
        data = deepcopy(source.to_dict())
        params = data['parameters']
        local = multiply(inverse_rigid(pose['trim']['mount']), pose['shield']['mount'])
        margin = manifest['edge_recess_mm']
        back = shield['atoms'][0]['dimensions'][1] / 2 - manifest['rear_overlap_mm']
        front = manifest.get('front_depth_mm', 6)
        cutters = deepcopy(shield['atoms'])
        names = {a['role']: 'shield_recess_' + a['role'] for a in cutters}
        for atom in cutters:
            atom['export'] = False
            atom['bevel'] = 0
            if atom['role'] == 'shield':
                atom['dimensions'][0] += 2 * margin
                atom['dimensions'][2] += 2 * margin
                atom['dimensions'][1] = back + front
                atom['location'][1] = (back - front) / 2
            else:
                # Extend the pointed silhouette slightly beyond the shield;
                # the remaining trim meets its rear, never the visible face.
                atom['dimensions'][1] = 14
                atom['frame_mm'][2][3] -= margin
            atom['role'] = names[atom['role']]
            atom['frame_mm'] = multiply(local, atom.get('frame_mm', identity()))
        params['atoms'].extend(cutters)
        cutter_operations = [
            dict(op, target=names[op['target']], operand=names[op['operand']])
            for op in shield['operations']]
        recess = dict(target='hem_trim', operand=names['shield'],
                      operation='DIFFERENCE', solver='EXACT')
        if manifest.get('recess_before_cape_cuts'):
            index = next(i for i, op in enumerate(params['operations'])
                         if op['operand']=='waist_wrap_limit')
            params['operations'].insert(index, recess)
            params['operations'] = cutter_operations + params['operations']
        else:
            params['operations'].extend(cutter_operations + [recess])
        params['shield_trim_fit'] = dict(
            source=source.reference, source_sha256=source.sha256,
            shield=pose['shield']['part'], shield_sha256=pose['shield']['definition_sha256'],
            shield_in_trim_frame=local, seed=seed,
            edge_recess_mm=margin, rear_overlap_mm=manifest['rear_overlap_mm'])
        params['provenance'] += (' Shield-shaped recess hides the vertical trim behind the shield '
                                 'while retaining rear contact. Shield pose and concealed lower '
                                 'join unchanged. Visual-only.')
        data.update(version=manifest['version'], name='Mail edging recessed behind the shield')
        result.append(finish(data))
    return result
