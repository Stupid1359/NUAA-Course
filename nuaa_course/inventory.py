from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_inventory(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "replay_inventory.json"
    if not path.exists():
        return {"lessons": []}
    return json.loads(path.read_text(encoding="utf-8"))


def lesson_rows(output_dir: Path) -> list[dict[str, Any]]:
    inventory = read_inventory(output_dir)
    rows: list[dict[str, Any]] = []
    for lesson in inventory.get("lessons", []):
        lesson_id = str(lesson.get("id"))
        lesson_dir = output_dir / "lessons" / lesson_id
        subtitle_path = lesson_dir / "raw" / "subtitle.json"
        transcript_path = lesson_dir / "raw" / "transcript.txt"
        subtitle_count = 0
        if subtitle_path.exists():
            body = json.loads(subtitle_path.read_text(encoding="utf-8"))
            subtitle_count = len(body.get("data", [])) if isinstance(body, dict) else 0
        rows.append({
            "id": lesson_id,
            "date": lesson.get("courBeginTime", ""),
            "number": lesson.get("letiNumber", ""),
            "subtitle_count": subtitle_count,
            "subtitle_file": subtitle_path.exists(),
            "transcript_file": transcript_path.exists(),
            "complete": subtitle_path.exists() and transcript_path.exists() and subtitle_count > 0,
        })
    return rows


def summarize(output_dir: Path) -> dict[str, int]:
    rows = lesson_rows(output_dir)
    return {
        "lessons": len(rows),
        "complete": sum(row["complete"] for row in rows),
        "empty": sum(row["subtitle_file"] and row["subtitle_count"] == 0 for row in rows),
        "missing": sum(not row["subtitle_file"] for row in rows),
    }
