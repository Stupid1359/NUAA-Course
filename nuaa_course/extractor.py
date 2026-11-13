from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import PACKAGE_ROOT

EXTRACTOR = PACKAGE_ROOT / "skills" / "nuaa-vod-summarizer" / "scripts" / "extract_nuaa_vod.py"


def extractor_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).with_name("nuaa-course-worker.exe")), "--extract-worker"]
    return [sys.executable, "-u", str(EXTRACTOR)]


def run_extractor(
    url: str,
    output_dir: Path,
    profile_dir: Path,
    settings: dict[str, Any],
    *,
    skip_existing: bool = False,
    lesson_id: str | None = None,
) -> int:
    command = [
        *extractor_command(),
        url,
        "--output-dir",
        str(output_dir),
        "--browser-runtime-auth",
        "--browser-channel",
        str(settings["browser_channel"]),
        "--user-data-dir",
        str(profile_dir),
        "--manual-wait-seconds",
        str(settings["manual_wait_seconds"]),
        "--extra-wait-ms",
        str(settings["extra_wait_ms"]),
        "--timeout-ms",
        str(settings["timeout_ms"]),
        "--batch",
    ]
    if skip_existing:
        command.append("--skip-existing")
    if lesson_id:
        command.extend(["--subtitle-course-id", str(lesson_id)])
    environment = dict(os.environ)
    environment["PYTHONUTF8"] = "1"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, cwd=str(PACKAGE_ROOT), env=environment)
    return result.returncode
