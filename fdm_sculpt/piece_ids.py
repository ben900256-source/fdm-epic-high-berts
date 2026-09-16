"""Persistent short handles for exact pieces in local viewer reviews."""
import json
from pathlib import Path
import re
import threading

LOCK = threading.Lock()


def annotate(review, directory):
    """Add IDs without changing the geometry revision or source manifest."""
    path = Path(directory)/'piece-ids.json'
    with LOCK:
        records = json.loads(path.read_text()) if path.exists() else {}
        original = dict(records)
        by_key = {tuple(record['key']): handle for handle, record in records.items()}
        next_id = max((int(handle, 16) for handle in records), default=0)+1
        identifiers = {}
        for placement in review['assembly']['placements']:
            asset = review['assets'][placement['part']]
            counts = {}
            handles = []
            for piece in asset.get('pieces') or [dict(role=None)]:
                role = piece['role']
                occurrence = counts.get(role, 0)
                counts[role] = occurrence+1
                key = (review['assembly']['assembly_id'], placement['instance_id'],
                       placement['part'].rsplit('@', 1)[0], role, occurrence)
                handle = by_key.get(key)
                if handle is None:
                    handle = f'{next_id:04X}'
                    next_id += 1
                    by_key[key] = handle
                records[handle] = dict(key=list(key), assembly_id=key[0], instance_id=key[1],
                                       part=placement['part'], geometry_role=role,
                                       occurrence=occurrence, revision=review['revision'],
                                       definition_sha256=placement['definition_sha256'])
                handles.append(handle)
            identifiers[placement['instance_id']] = handles
        if records != original:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(records, indent=2), encoding='utf-8')
            temporary.replace(path)
    return dict(review, piece_ids=identifiers)


def lookup(handle, directory):
    handle = handle.strip().removeprefix('#').upper().removeprefix('0X')
    if not re.fullmatch(r'[0-9A-F]+', handle):
        raise ValueError('Expected a hexadecimal piece ID')
    handle = f'{int(handle, 16):04X}'
    path = Path(directory)/'piece-ids.json'
    with LOCK:
        records = json.loads(path.read_text()) if path.exists() else {}
    if handle not in records:
        raise ValueError('Unknown piece ID: '+handle)
    return dict(id=handle, **records[handle])
