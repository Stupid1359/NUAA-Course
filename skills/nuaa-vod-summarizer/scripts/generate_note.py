from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_note_context(lesson_dir: Path) -> str:
    """Assemble the full context needed to generate a Markdown note."""
    metadata = load_json(lesson_dir / "metadata.json")
    transcript_path = lesson_dir / "raw" / "transcript.txt"

    transcript = ""
    if transcript_path.exists():
        transcript = transcript_path.read_text(encoding="utf-8")

    parts: list[str] = []

    # Metadata block
    parts.append("## Lesson Metadata\n")
    parts.append(f"- **课程**: {metadata.get('subjName', '')}")
    parts.append(f"- **教师**: {', '.join(metadata.get('teacNames', []))}")
    parts.append(f"- **时间**: {metadata.get('courBeginTime', '')} - {metadata.get('courEndTime', '')}")
    parts.append(f"- **节次**: 第{metadata.get('letiNumber', '')}节")
    parts.append(f"- **周次**: 第{metadata.get('zc', '')}周")
    parts.append(f"- **教室**: {metadata.get('clroName', '')}")
    parts.append(f"- **课程序号**: {metadata.get('teclCode', '')}\n")

    parts.append("## Transcript\n")
    parts.append(transcript)
    parts.append("")

    return "\n".join(parts)


NOTE_PROMPT = """## Task

Generate a concise student-facing Markdown lecture handout from the transcript above.

## Note Structure

Use this compact structure. Omit sections without useful content:

```markdown
# {课程名} — 第{节次}节 ({日期})

## 本节内容

{用简短段落说明本节课讲了什么，以及内容之间的关系}

## 重点概念

- **概念或术语**：用一句话解释

## 课堂例子或作品

{保留课堂中出现的电影、导演、作品、历史事件或其他例子}

## 需要记住的内容

- ...

## 课程安排

{只记录字幕中明确出现的作业、考试、截止日期或教师通知}

## 考试与成绩相关事项

{明确说明本节是否提及考试、作业、报告、期末考核、成绩比例、出勤成绩影响或提交时间。每项内容附带 [MM:SS] 时间戳，并引用教师原话；没有提及时明确写出“本节字幕中未提及”。字幕识别不清的原话放入“待核对”。}

## 待核对

- ...
```

## Rules

1. **Never invent content.** Every claim must be traceable to the transcript.
2. **Rephrase in your own words.** Do not copy ASR output verbatim as final prose.
3. **Flag ASR noise.** If a sentence is garbled, mark it under "待核对" rather than guessing.
4. **Keep student-facing.** Do not expose API fields, internal paths, or workflow details.
5. **Record assignments and examinations only when explicit.**
6. **Add moderate timestamps.** Use `[MM:SS]` beside important concepts, film examples, teacher conclusions, assignments, and major topic transitions. Do not timestamp every sentence.
7. **Write in Chinese** with established foreign terms and film titles unchanged where appropriate.

---

Generate the note now based on the lesson context above.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare context for NUAA lesson note generation.")
    parser.add_argument("lesson_dir", help="Path to a lesson directory (e.g., work/<course-id>/lessons/<lesson-id>)")
    parser.add_argument("--print-context", action="store_true", help="Print full context for the agent.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the note generation prompt template.")
    args = parser.parse_args()

    lesson_dir = Path(args.lesson_dir).resolve()
    if not lesson_dir.is_dir():
        print(f"Not a directory: {lesson_dir}", file=__import__("sys").stderr)
        return 1

    if args.print_prompt:
        print(NOTE_PROMPT)
        return 0

    if args.print_context:
        print(build_note_context(lesson_dir))
        return 0

    # Default: print context then prompt
    print(build_note_context(lesson_dir))
    print("\n---\n")
    print(NOTE_PROMPT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
