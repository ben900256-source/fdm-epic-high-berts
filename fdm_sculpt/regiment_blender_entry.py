"""Background Blender entry, also used to verify saved provenance."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.regiment_blender import run

if __name__ == "__main__":
    run(json.loads(Path(sys.argv[sys.argv.index("--")+1]).read_text(encoding="utf-8")))
