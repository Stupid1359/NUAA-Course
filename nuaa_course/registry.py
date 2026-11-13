from __future__ import annotations

from typing import Any


def resolve_course(registry: dict[str, Any], key: str) -> tuple[str, dict[str, Any]] | None:
    courses = registry.get("courses", {})
    if key in courses:
        return key, courses[key]
    for name, info in courses.items():
        if key == str(info.get("teclId", "")) or key in str(info.get("url", "")):
            return name, info
    return None


def course_output_dir(info: dict[str, Any], resolve_path) -> Any:
    return resolve_path(info["vod_output_dir"])
