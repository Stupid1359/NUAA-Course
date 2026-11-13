---
name: obsidian-course-vault
description: Put concise NUAA course lecture handouts into an existing Obsidian vault.
---

# Obsidian Course Vault (NUAA)

将 NUAA VOD 字幕整理完成的 Markdown 讲义放入 `<vault-dir>` 指定的 Obsidian 目录。

Assume commands run from this skill root.

## Core Boundary

- The agent writes the handout and copies it into the course's `课次` directory.
- Keep the existing vault structure. Do not create concept pages, graph indexes, admin pages, or extra templates for this task.
- A lesson without usable subtitles stays in `待整理回放.md`.

## Main Commands

**Optional extraction sync**:

```powershell
python scripts\sync_nuaa_course.py --vault-dir "<vault-dir>" --course-name "<课程名>" --vod-output-dir "<vod-output-dir>"
```

同步脚本使用 `01-Courses` 目录结构。采用 `课程讲义` 目录结构时，将完成的讲义写入 `<vault-dir>\课程讲义\<课程名>\课次\`。

## Workflow

### 1. Extract and write notes

Use `nuaa-vod-summarizer` to extract lessons, then write `note.md` for each finished lesson.

Read the full transcript, write one concise handout, and save it as:

```text
<vault-dir>\课程讲义\<课程名>\课次\<日期> <课程名> 第<节次>节.md
```

Update `待整理回放.md` only when a lesson has no usable transcript. Keep the existing course overview and progress files unchanged unless the user asks for index maintenance.

## Required Replay Diagnosis

Before syncing any lesson note, classify each lesson into exactly one of:

1. **`waiting_transcript`** — subtitles not yet available
2. **`partial_transcript`** — subtitle exists but incomplete or garbled
3. **`transcript_only`** — has transcript but no note yet

This classification is produced by `nuaa-vod-summarizer`. Downstream vault sync must consume this classification — do not copy placeholder or diagnostic notes into the vault as finished content.

## Course Affairs

Include homework, examinations, deadlines, or teacher notices in the handout only when they appear in the transcript. Do not maintain a separate affairs table for this task.

## Authoring Contract

When writing notes for vault integration:

- Read the full transcript before writing.
- Use short headings and paragraphs.
- Preserve film titles, people, dates, movements, terms, examples, and teacher emphasis.
- Add a moderate number of timestamps such as `[00:18]` or `[18:20]` beside important concepts, film examples, teacher conclusions, assignments, and major topic transitions. Do not add a timestamp to every sentence.
- When enriching an existing handout, add transcript-supported explanations, film or concept comparisons, analysis angles, review prompts, and links with earlier lessons while keeping the same simple vault structure.
- Add a separate `## 考试与成绩相关事项` section to every handout. State whether the lesson mentions examinations, homework, reports, final assessments, grading, attendance consequences, or submission deadlines. For every mentioned item, give a timestamp and quote the teacher's original words from the transcript. If the lesson has no such mention, state that explicitly. Mark garbled or incomplete quotations as needing verification.
- Put uncertain items under `待核对`.
- Do not expose raw ASR fragments, OCR snippets, or workflow notes.

## Final Note Quality Gate

A lesson is unfinished if it contains:

- Raw ASR/OCR snippets
- Empty template sections
- Repeated generic study advice
- Obvious subtitle noise
- Process commentary

For math-heavy courses, the note must reconstruct concrete mathematical objects, equations, proofs, and examples, or remain a draft.

## Course-Domain Reconstruction Guidance

- **Math and statistics:** reconstruct objects, definitions, assumptions, equations, theorems, proof ideas, examples, counterexamples, symbol meanings.
- **Engineering and computer science:** reconstruct system components, algorithms, design constraints, implementation steps, trade-offs.
- **Humanities and social sciences:** reconstruct concepts, arguments, background, author positions, evidence, comparisons.
- **Ideological and political courses:** reconstruct policy concepts, theoretical claims, historical context, named documents/events, exam-oriented formulations.
- **Language, writing, and communication courses:** reconstruct vocabulary, rhetorical patterns, text structure, examples, correction points.
- **Lab, design, or project courses:** reconstruct task goals, deliverables, tools, operation steps, grading criteria.

## Output Rules

- Save only finished handouts in `课程讲义\<课程名>\课次`.
- Keep extraction JSON, raw subtitles, and temporary files in the source project's `work` directory.
- Do not create concept pages or graph links unless the user explicitly requests them.
- Use Markdown headings and lists that match the existing vault style.

## Existing Vault Structure

```
<vault-dir>\
  00-Home.md
  课程讲义\
    <课程名>\
      00-课程总览.md
      01-观看进度.md
      待整理回放.md
      课次\
        <日期> <课程名> 第<节次>节.md
      笔记\
        <章节或主题>.md
  课程进度\
```

## Course Identity Rule

Course title — not `course_id`, lecturer, schedule, or classroom — determines identity. Multiple source URLs can feed the same titled course as long as provenance is preserved in sync metadata.

## Failure Rules

- Never create the vault inside `nuaa-vod-summarizer/work/`.
- If the transcript is empty or near-empty, update `待整理回放.md` and do not create a placeholder handout.
- Do not overwrite an existing handout unless the user requests replacement.
- Keep the original transcript and extraction artifacts in the source project.

## Integration with nuaa-vod-summarizer

The bridge is the `course.json` + `replay_inventory.json` + per-lesson `note.md`:

```
vod-output-dir/
  course.json              ← course identity
  replay_inventory.json    ← full lesson list
  lessons/<id>/
    metadata.json          ← lesson metadata
    note.md                ← finished Markdown note (the source of truth)
```

Only lessons with `note.md` present and non-empty are treated as "finished" and synced into the vault.
