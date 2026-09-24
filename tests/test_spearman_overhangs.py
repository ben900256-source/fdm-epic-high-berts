import json
import os
from pathlib import Path
import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.components.parts import catalog, resolve_assembly
from fdm_sculpt.components.spearman_overhangs import revised_parts, refined_parts, sleeve_part, deposited_shield_part

ROOT = Path(__file__).resolve().parents[1]






def test_new_ramps_keep_original_geometry_and_landmarks():
    definitions = catalog()
    for part in revised_parts(definitions, 1001):
        new = part.to_dict()['parameters']
        old = definitions[new['overhang_revision']['source']].to_dict()['parameters']
        assert new['landmarks'] == old['landmarks']
        assert new['operations'] == old['operations']
        if part.component_id != 'aurelian.spear':
            assert new['atoms'][:len(old['atoms'])] == old['atoms']
            assert len(new['atoms']) > len(old['atoms'])
