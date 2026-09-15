"""Prepare a checked original-mail figure cache from pinned review evidence."""
import argparse
import json
from pathlib import Path
import subprocess
from fdm_sculpt.atelier import file_hash
from fdm_sculpt.review import find_blender


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('review', 'prepared-build', 'mail-cache', 'exterior-proof', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    review, output = args.review.resolve(), args.output.resolve()
    job = json.loads((review/'assembly-job.json').read_text())
    if job['seed'] != args.seed:
        raise ValueError('seed must match pinned review')
    if not json.loads(args.exterior_proof.read_text())['passes']:
        raise ValueError('original mail exterior comparison must pass')
    blender = find_blender()
    if 'Blender 5.1.2' not in subprocess.check_output([str(blender), '--version'], text=True):
        raise ValueError('Blender 5.1.2 required')
    output.mkdir(parents=True, exist_ok=False)
    worker = Path('fdm_sculpt/modular_print_original.py').resolve()
    inputs = dict(seed=args.seed, review=str(review), assembly_job_sha256=file_hash(review/'assembly-job.json'),
                  source_scene_sha256=file_hash(review/'assembly.blend'),
                  mail_cache_sha256=file_hash(args.mail_cache), exterior_proof_sha256=file_hash(args.exterior_proof),
                  prepared_inputs_sha256=file_hash(args.prepared_build/'build-inputs.json'),
                  prepared_parts_sha256=file_hash(args.prepared_build/'internal/prepared-parts.blend'),
                  prepared_base_scene_sha256=file_hash(args.prepared_build/'internal/union-failure.blend'),
                  generator_sha256={p.name:file_hash(p) for p in [worker, Path('fdm_sculpt/modular_print_blender.py')]})
    (output/'build-inputs.json').write_text(json.dumps(inputs, indent=2))
    command = [str(blender), '--background', str(review/'assembly.blend'), '--python-exit-code', '1',
               '--python', str(worker), '--', str(review), str(args.prepared_build.resolve()),
               str(args.mail_cache.resolve()), str(output)]
    with (output/'blender.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)


if __name__ == '__main__':
    main()
