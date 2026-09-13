"""Probe evaluated cached handles inside the actual posed palm silhouettes."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fdm_sculpt.atelier import engine_hash
from fdm_sculpt.components.parts import catalog, cache_key
from fdm_sculpt.army import load_assembly

definitions = catalog()
meshes = {}


def tree(placement):
    reference = placement['part']
    if reference not in meshes:
        definition = definitions[reference]
        directory = ROOT/'out/part-cache'/cache_key(definition, engine_hash(definition))
        asset = json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'), link=True) as (_, loaded):
            loaded.collections = [asset['visual_collection']]
        meshes[reference] = list(loaded.collections[0].objects)
    vertices, faces = [], []
    for obj in meshes[reference]:
        offset = len(vertices)
        frame = Matrix(placement['mount']) @ obj.matrix_basis
        vertices.extend(frame @ v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in face.vertices] for face in obj.data.polygons)
    return BVHTree.FromPolygons(vertices, faces)


checks = 0
for name in ('elf-archer', 'elf-unit-archers', 'elf-archer-variants', 'elf-archer-sergeant'):
    assembly = load_assembly(ROOT/f'specs/{name}.json', definitions)
    placements = {p['instance_id']: p for p in assembly['placements']}
    for instance, bow in placements.items():
        if not instance.endswith('/bow'):
            continue
        prefix = instance[:-3]
        arm = placements[prefix+'bow-arm']
        hand = tree(arm)
        frame = Matrix(arm['mount'])
        grip = Vector(definitions[arm['part']].to_dict()['parameters']['landmarks']['grip'])
        for slot in ('bow', 'bow-ferrule'):
            equipment = tree(placements[prefix+slot])
            for height in (-.3, 0, .3):
                center = frame @ (grip + Vector((0, 0, height)))
                for step in range(16):
                    # Avoid rays landing exactly on cylindrical polygon seams.
                    angle = (step+.37)*math.tau/16
                    direction = frame.to_3x3() @ Vector((math.cos(angle), math.sin(angle), 0))
                    # Starting within the grasp, compare the first outward surfaces.
                    skin = hand.ray_cast(center, direction)[0]
                    handle = equipment.ray_cast(center, direction)[0]
                    assert skin is not None and handle is not None, (name, instance, slot, height, step, list(center), skin, handle)
                    assert (handle-center).length < (skin-center).length-.015, (name, instance, slot, height, step)
                    checks += 1
(ROOT/'out/bow-grip-geometry-check.json').write_text(json.dumps(dict(passes=True, radial_checks=checks), indent=2)+'\n')
print('BOW_GRIPS_WITHIN_POSED_HANDS', checks)
