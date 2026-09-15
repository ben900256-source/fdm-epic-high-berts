"""Attach each cached figure to the base with a separately checked Exact union."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt import modular_print_cached as cached
from fdm_sculpt.modular_print_blender import ordered_fuse


def sequential_stand(name, objects, collection, **options):
    result = objects[0]
    for index, figure in enumerate(objects[1:], 1):
        print('ATTACHING_FIGURE', index, flush=True)
        result = ordered_fuse(f'{name}/figure-{index}', [result, figure], collection,
                              small_closure=True, preserve_vertices=True)
        folder = Path(bpy.context.scene['manufacturing_output_directory'])
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'checked-stand-{index}.blend'))
    return result


if __name__ == '__main__':
    cached.ordered_fuse = sequential_stand
    cached.run(*sys.argv[sys.argv.index('--')+1:])
