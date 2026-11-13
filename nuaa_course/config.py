from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = Path(sys.executable).resolve().parent.parent if getattr(sys, "frozen", False) else PACKAGE_ROOT.parent
DATA_ROOT = Path(os.environ["NUAA_COURSE_DATA_DIR"]).resolve() if "NUAA_COURSE_DATA_DIR" in os.environ else (
    WORKSPACE_ROOT / "data"
)
SETTINGS_PATH = DATA_ROOT / "settings.local.json"
REGISTRY_PATH = DATA_ROOT / "courses.local.json"
LEGACY_REGISTRY_PATH = DATA_ROOT / "courses.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "browser_channel": "msedge",
    "manual_wait_seconds": 120,
    "extra_wait_ms": 8000,
    "timeout_ms": 60000,
    "output_root": "courses",
}


def load_settings() -> dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.exists():
        settings.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_registry() -> dict[str, Any]:
    path = REGISTRY_PATH if REGISTRY_PATH.exists() else LEGACY_REGISTRY_PATH
    if not path.exists():
        return {"courses": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("courses", {})
    return data


def save_registry(registry: dict[str, Any]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_path(value: str | Path) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    return path if path.is_absolute() else DATA_ROOT / path


def output_root(settings: dict[str, Any]) -> Path:
    return resolve_path(settings["output_root"])
