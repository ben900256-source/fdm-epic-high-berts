"""Locate the installed Blender executable without modifying its settings."""
from __future__ import annotations
import os
from pathlib import Path
import shutil


def find_blender(configured: str | Path | None = None) -> Path | None:
    configured_value = configured or os.environ.get("BLENDER_BIN")
    candidates = (
        Path(configured_value).expanduser() if configured_value else None,
        Path(found) if (found := shutil.which("blender")) else None,
        Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
        Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        Path("/usr/bin/blender"),
    )
    return next(
        (candidate.resolve() for candidate in candidates if candidate and candidate.is_file()),
        None,
    )
