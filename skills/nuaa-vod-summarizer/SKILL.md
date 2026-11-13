---
name: nuaa-vod-summarizer
description: Extract NUAA Feitian Cloud Classroom subtitles and turn them into concise course lecture notes.
---

# NUAA VOD Summarizer

Use this skill for NUAA Feitian Cloud Classroom pages. Both URL formats are supported:

```text
https://ft.nuaa.edu.cn/jy-application-vod-he-ui/#/video-detail?id=<course-id>
https://ft.nuaa.edu.cn/jy-application-resourcemanage-ui/#/play-center?teclId=<course-id>
```

The API base (`/jy-application-vod-he` or `/jy-application-resourcemanage`) is auto-detected from the URL.

Assume commands run from this skill root. Otherwise use the absolute path to `scripts/`.

## Core Boundary

- Let scripts handle browser login reuse, API discovery, replay metadata extraction, subtitle export, and artifact writes.
- Let the agent handle transcript diagnosis, obvious terminology correction, and final Markdown prose.
- Write a concise lecture handout that follows the actual subtitle content.
- Do not write a note when subtitles are missing, empty, or clearly incomplete.

## Main Commands

日常使用优先通过项目统一入口：

```powershell
.\scripts\nuaa-course.ps1 add "<course-url>" --name "课程名称"
.\scripts\nuaa-course.ps1 fetch "课程名称" --skip-existing
```

以下命令用于直接调用底层抽取脚本。

### Probe one lesson (quick test)

```powershell
python scripts\extract_nuaa_vod.py "<video-detail-url>" --output-dir "<output-dir>" --browser-runtime-auth --manual-wait-seconds 60
```

### Extract ALL lessons in the course list (batch)

```powershell
python scripts\extract_nuaa_vod.py "<video-detail-url>" --output-dir "<output-dir>" --browser-runtime-auth --manual-wait-seconds 60 --batch --skip-existing
```

### Extract a specific lesson by ID

```powershell
python scripts\extract_nuaa_vod.py "<video-detail-url>" --output-dir "<output-dir>" --subtitle-course-id <lesson-id> --manual-wait-seconds 10
```

## Output Structure

```
<output-dir>/
  course.json                          # course-level metadata
  replay_inventory.json                # full lesson list with transfer flags
  raw/
    page.json                          # parsed URL info
    captured_responses.json            # all captured API responses
    storage_state.json                 # browser storage state
    responses/                         # individual response files
  lessons/
    <lesson_id>/
      metadata.json                    # lesson metadata
      raw/
        subtitle.json                  # raw subtitle API response
        transcript.txt                 # cleaned transcript with timestamps
      note.md                          # concise Markdown lecture handout
```

## Supported Platforms

Two UI/API pairs are supported, auto-detected from the URL:

| UI host | API base | Main route |
| --- | --- | --- |
| `ft.nuaa.edu.cn/jy-application-vod-he-ui` | `/jy-application-vod-he` | `#/video-detail?id=<teclId>` |
| `ft.nuaa.edu.cn/jy-application-resourcemanage-ui` | `/jy-application-resourcemanage` | `#/play-center?teclId=<teclId>` |

Known API families (both platforms share similar paths under their API base):

- `/v1/subject_vod_list` — lesson list (vod-he)
- `/v1/group_subject_vod_list` — lesson list (resourcemanage)
- `/v1/course_vod_videoinfos` — lesson video metadata
- `/v1/course_vod_urls` — playback URLs
- `/v1/course_vod_subtitle` — AI subtitles
- `/v1/courseware/upload/list` — courseware list
- `/v1/courseware/downLoad` — courseware download
- `/v1/course/verify` — course access check

## Workflow

1. Open the supplied URL (`video-detail` or `play-center`) in a persistent Chromium context.
2. If needed, complete NUAA login in the browser window.
3. Capture NUAA VOD API responses while the page loads.
4. Auto-detect API base from URL markers.
5. Enumerate all lessons in the course list.
6. For each lesson, fetch `<api_base>/v1/course_vod_subtitle` and classify the response.
7. Save subtitle JSON and cleaned transcript per lesson.
8. Generate a concise Markdown lecture handout from each usable transcript.

## Required Replay Diagnosis

Before building any note, classify each lesson into exactly one of:

1. **`waiting_transcript`** — subtitles not yet available (no `courTransferFlag`, or fetch returned empty)
2. **`partial_transcript`** — subtitle exists but is clearly incomplete, garbled beyond repair, or covers only a fraction of the lesson
3. **`transcript_only`** — has complete transcript but no note written yet

Downstream note logic must consume this classification instead of recomputing route decisions.

## Lecture Note Rules

- Read the full `transcript.txt` before writing.
- Correct obvious ASR term errors when the course context makes the intended term clear.
- Preserve the lecture's main order and important examples.
- Keep only useful student-facing content; remove repeated spoken filler and subtitle noise.
- Use short headings and paragraphs. Do not create a complex concept graph or a separate research report.
- Add a moderate number of timestamps such as `[00:18]` or `[18:20]` beside important concepts, film examples, teacher conclusions, assignments, and the start of a major topic. Do not timestamp every sentence.
- When the user asks to enrich a handout, add transcript-supported knowledge explanations, comparisons between concepts or films, analysis angles, review prompts, and links between the current lesson and earlier lessons. Keep the added content tied to the lecture.
- Add a separate `## 考试与成绩相关事项` section to every handout. State whether the lesson mentions examinations, homework, reports, final assessments, grading, attendance consequences, or submission deadlines. For every mentioned item, give a timestamp and quote the teacher's original words from the transcript. If the lesson has no such mention, state that explicitly. Mark garbled or incomplete quotations as needing verification.
- Keep formulas in `$...$` or `$$...$$` when formulas occur.
- If `transcript.txt` is missing, empty, or near-empty, classify the lesson as `waiting_transcript` and do not create a handout.

## Authoring Contract

When writing the student-facing Markdown handout:

- Start with a level-one heading containing the lesson title.
- Use this compact structure when the transcript supports it:
  - `## 本节内容`
  - `## 重点概念`
  - `## 课堂例子或作品`
  - `## 需要记住的内容`
  - `## 待核对`
- Omit headings that have no useful content.
- Preserve film titles, people, dates, movements, terms, and teacher-emphasized conclusions.
- Add timestamps to the corresponding bullets or paragraphs when the transcript provides a reliable time range.
- Record assignments or exam information in a short `## 课程安排` section only when the transcript contains them.
- Write directly for the student. Do not expose raw ASR lines or workflow notes.

## Handout Quality Gate

A student-facing handout is ready when it:

- accurately reflects the usable transcript;
- contains the lesson's central subject and important supporting details;
- removes subtitle noise and obvious ASR errors;
- remains readable as a short handout;
- places uncertain information under `待核对`.

## Course-Domain Reconstruction Guidance

- **Math and statistics:** reconstruct objects, definitions, assumptions, equations, theorems, proof ideas, examples, counterexamples, symbol meanings, and links between results.
- **Engineering and computer science:** reconstruct system components, algorithms, design constraints, implementation steps, experiment setup, failure cases, trade-offs, and how formulas/code relate to the design.
- **Humanities and social sciences:** reconstruct concepts, arguments, historical/institutional background, author positions, evidence, comparisons, cases, and the teacher's evaluative emphasis.
- **Ideological and political courses:** reconstruct policy concepts, theoretical claims, historical context, named documents/events, value judgments, exam-oriented formulations, and examples used to explain abstract claims.
- **Language, writing, and communication courses:** reconstruct vocabulary, rhetorical patterns, text structure, examples, correction points, practice requirements, and teacher feedback.
- **Lab, design, or project courses:** reconstruct task goals, deliverables, tools, operation steps, data requirements, safety/format constraints, grading criteria, and troubleshooting advice.

## Transcript-Only Rule

When a lesson is classified as `transcript_only`:

- Read the transcript and write the compact handout structure only where the content supports it.
- Do not fill empty sections with generic study advice.

## PPT / Courseware Rule

- Prefer teacher audio/subtitle stream by default.
- Treat PPT and courseware as **auxiliary only**, even when available.
- PPT may help with term spelling, page/book titles, formula symbols, and logistics screenshots.
- PPT **must not** decide section boundaries, lesson mainline, concept generation, or completion state.

## Failure Rules

- If authentication fails or no VOD API responses are captured, keep `raw/page.json` and explain that a logged-in browser session is required.
- If subtitle data is absent for a lesson, mark it as no-subtitle and skip.
- If subtitle text is empty or near-empty, do not produce a final note.
- If transcript coverage is clearly partial, keep the lesson in the pending list and do not create a finished handout.
- Treat courseware/PPT as auxiliary only; it must not replace transcript evidence.
- If session reuse fails, rerun with `--browser-runtime-auth`.

On Windows, prefer PowerShell commands. For inline Python, use:

```powershell
@'
print("hello")
'@ | python -
```
