# Epic High Berts

Five original high-elf spearmen, approximately 8 mm sole-to-eye, fused to a
20 × 5 × 1 mm strip. Python recipes generate an orbitable Blender scene and
trial-print files for a five-tool Prusa XL using tool 2's 0.25 mm nozzle.

![Five spearmen with seahorse shields](docs/images/three-quarter.png)

Revision 9 has five individual poses, broad pointed shields with raised
seahorse insignia, shoulder-hung flared capes, rounded torso and shoulder armor,
continuous spear grips, and curved pointed helmets with integrated brows and
cheek guards. Earlier recipes remain pinned for reproducibility.

Current status: visual proof with mesh and feature checks. The latest revision
has not yet completed slicing validation or a physical trial print. A successful
review command alone does not label the model **digitally validated**.

## Run a visual review

Use Python 3.13 and Blender **5.1.2**. Set `BLENDER_BIN` if Blender is outside the
standard installation paths. From this repository:

```powershell
py -m pip install -e ".[test]"
py -m fdm_sculpt.regiment review specs/elf-spearman-proof-v9.json --seed 1001 --output out/elf-v9-review
py -m pytest
```

Open `out/elf-v9-review/internal/elf-spearman-proof.blend` and orbit the selected
fused strip with the middle mouse button. Technical PNGs appear in `previews/`.
Use a fresh output directory for every generation. Hidden `SOURCE_PRIMITIVES`
retain the parameterized geometry and Exact CSG operands; `EVALUATED_EXPORT`
contains the printable solid. Revise recipes and regenerate instead of editing
mesh vertices.

## Prepare a trial print

The print adapter currently targets Windows and PrusaSlicer **2.9.5**, with
these existing installed presets:

- Printer: `Original Prusa XL - 5T 0.25 nozzle - Miniatures`
- Print: `0.05mm ULTRADETAIL @XLIS 0.25 - Balanced Miniatures`
- Filament: `Generic PLA @XL`

These locally configured presets are prerequisites; their private snapshots are
not distributed in this source repository. The adapter resolves inheritance and
writes hashed build-local snapshots without modifying the installed presets.
It preserves the nozzle array `0.4,0.25,0.4,0.4,0.4`, selects tool 2, and retains
0.05 mm layers, a 0.14 mm first layer, three perimeters, conservative speeds and
a 6 mm brim. Automatic supports, the wipe tower and binary G-code are disabled.

```powershell
py -m fdm_sculpt.regiment build specs/elf-spearman-proof-v9.json --seed 1001 --output out/elf-v9-trial
py -m fdm_sculpt.regiment build specs/elf-spearman-proof-v9.json --seed 1001 --output out/elf-v9-repeat --no-renders --no-slice
py -m fdm_sculpt.regiment validate out/elf-v9-trial --compare out/elf-v9-repeat
```

The build emits mono STL, generic 3MF, a PrusaSlicer project 3MF and plain-text
G-code. Validation reopens artifacts, checks tool 2 (`T1`) extrusion, compares
same-seed geometry, and inspects layer coverage, islands and unsupported growth.
Only a passing validation manifest earns the label **digitally validated**.
Print upright with the strip flat on the bed and PLA loaded in tool 2.

## Source and evidence

- [Construction and validation rules](docs/construction.md)
- [Technical proof evidence](proof/review.json)
- [Helmet and grip detail](docs/images/face-grip-detail.png)
- [Seahorse shield detail](docs/images/seahorse-shield.png)
- [Shoulder cape detail](docs/images/cape-shoulders.png)

The component library is Blender-free and pins every revision's definition and
resolved-plan hashes. Integration tests can reopen a generated scene by setting
`ELF_PROOF_BUILD` to its absolute build directory before running pytest.
Historical revision-specific tests skip when given a different revision.

This repository contains the elf effort and its required generic primitive,
mesh and file-format support. Generated builds and local slicer settings stay
under ignored `out/` directories. Archers and command strips follow acceptance
of the spearman proof; cavalry, multicolor and commercial packaging are outside
this milestone.
