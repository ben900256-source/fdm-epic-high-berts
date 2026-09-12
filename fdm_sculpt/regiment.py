"""CLI for the internal elf spearman proof: review, build, validate."""
from __future__ import annotations
import argparse
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

from . import formats
from .prusa import sha256, slice_build
from .regiment_spec import RegimentSpec
from .review import find_blender


def generate(spec_path, *, seed, output, operation="build", renders=True, slice_model=True):
    spec = replace(RegimentSpec.load(spec_path), seed=seed)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh output directory; proof builds are immutable")
    internal = output/"internal"
    internal.mkdir(parents=True, exist_ok=True)
    spec_path = internal/"regiment-spec.json"
    spec_path.write_text(json.dumps(spec.to_dict(), sort_keys=True, indent=2)+"\n")
    job = dict(spec=spec.to_dict(), output=str(output), operation=operation, renders=renders)
    job_path = internal/"blender-job.json"
    job_path.write_text(json.dumps(job, sort_keys=True, indent=2)+"\n")
    package = Path(__file__).resolve().parent
    generator_files = [package/name for name in ("regiment.py","regiment_spec.py","regiment_blender.py",
                                                "regiment_provenance_entry.py","blender_backend.py",
                                                "components/elves.py","components/elves_v2.py",
                                                "components/elves_v3.py","components/elves_v4.py","components/elves_v5.py","components/elves_v6.py","components/elves_v7.py","components/elves_v8.py","components/elves_v9.py",
                                                "components/elves_v10.py","components/elves_v11.py","components/core.py","prusa.py",
                                                "regiment_validation.py","printability.py","regiment_visual.py")]
    generator_hashes = {str(p.relative_to(package)).replace('\\','/'):sha256(p) for p in sorted(generator_files)}
    (internal/"generator-hashes.json").write_text(json.dumps(generator_hashes,sort_keys=True,indent=2)+"\n")
    blender = find_blender()
    if blender is None:
        raise ValueError("Blender 5.1.2 is required")
    version = subprocess.run([str(blender), "--version"], capture_output=True, text=True, timeout=30)
    if "Blender 5.1.2" not in version.stdout:
        raise ValueError("Blender 5.1.2 is required")
    entry = Path(__file__).with_name("regiment_blender_entry.py").resolve()
    command = [str(blender), "--background", "--factory-startup", "--python-exit-code", "1",
               "--python", str(entry), "--", str(job_path)]
    log_path = internal/"blender.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
    (internal/"execution.json").write_text(json.dumps(dict(command=command, returncode=process.returncode), indent=2)+"\n")
    if process.returncode or "REGIMENT_BUILD_COMPLETE" not in log_path.read_text(encoding="utf-8",errors="replace"):
        raise RuntimeError(f"Blender proof failed; see {internal/'blender.log'}")
    provenance_entry = Path(__file__).with_name("regiment_provenance_entry.py").resolve()
    verification = subprocess.run([str(blender), "--background", str(internal/"elf-spearman-proof.blend"),
                                   "--python-exit-code", "1", "--python", str(provenance_entry), "--", str(output)],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  encoding="utf-8", errors="replace", timeout=120)
    (internal/"provenance.log").write_text(verification.stdout, encoding="utf-8")
    if verification.returncode or "REGIMENT_PROVENANCE_VERIFIED" not in verification.stdout:
        raise RuntimeError(f"saved Blender verification failed; see {internal/'provenance.log'}")
    if operation == "build":
        mesh = formats.read_stl(output/"elf-spearman-proof.stl")
        formats.write_3mf(output/"elf-spearman-proof.3mf", [formats.ColorVolume(
            "Aurelian leafguard proof", mesh, formats.Material("Single-color PLA", "#D2C5A2"))])
        formats.read_3mf(output/"elf-spearman-proof.3mf")
        if slice_model:
            slice_build(output)
    return dict(output=str(output), operation=operation,
                status="visual preview only; overlapping parts, not print validated" if operation == "preview"
                else "internal proof; validation pending")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for operation in ("preview", "review", "build"):
        command = sub.add_parser(operation)
        command.add_argument("spec", type=Path)
        command.add_argument("--seed", type=int, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--no-renders", action="store_true", help="geometry replay only")
        if operation == "build":
            command.add_argument("--no-slice", action="store_true", help="geometry replay only; cannot validate")
    validate = sub.add_parser("validate")
    validate.add_argument("build", type=Path)
    validate.add_argument("--compare", type=Path, required=True, help="independent same-seed build")
    assess = sub.add_parser("assess", help="inspect existing trial layers and support risks before final validation")
    assess.add_argument("build", type=Path)
    assess.add_argument("--support-audit", action="store_true", help="also generate a separate automatic-support diagnostic")
    args = parser.parse_args(argv)
    try:
        if args.operation == "assess":
            from .regiment_validation import assess_build
            result = assess_build(args.build, automatic_supports=args.support_audit)
        elif args.operation == "validate":
            from .regiment_validation import validate_build
            result = validate_build(args.build, args.compare)
        else:
            result = generate(args.spec, seed=args.seed, output=args.output, operation=args.operation,
                              renders=not args.no_renders, slice_model=not getattr(args,"no_slice",False))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("passes", True) else 1
    except Exception as exc:
        print(json.dumps(dict(ok=False, error=str(exc))), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
