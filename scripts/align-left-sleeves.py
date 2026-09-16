"""Align the current spearman cloth sleeves to their upper arms."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.sleeve_placement import align_left_sleeves

path=ROOT/'specs/elf-modular-visual.json'
assembly=align_left_sleeves(json.loads(path.read_text()),catalog())
path.write_text(json.dumps(assembly,indent=2)+'\n')
