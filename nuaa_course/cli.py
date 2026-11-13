from __future__ import annotations

import argparse
import importlib.util
from importlib.metadata import version
import re
import shutil
import sys
from pathlib import Path

from .config import load_registry, load_settings, output_root, resolve_path, save_registry
from .extractor import run_extractor
from .inventory import lesson_rows, summarize
from .registry import course_output_dir, resolve_course


def course_key(name: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", name, flags=re.UNICODE).strip("._")
    return value[:80] or "course"


def profile_for(output_dir: Path) -> Path:
    return output_dir / ".browser-profile"


def print_summary(name: str, output_dir: Path) -> None:
    stats = summarize(output_dir)
    print(
        f"课程：{name} | 课次：{stats['lessons']} | "
        f"字幕完成：{stats['complete']} | 空字幕：{stats['empty']} | 未生成：{stats['missing']}"
    )


def command_doctor(_: argparse.Namespace) -> int:
    settings = load_settings()
    print(f"Python：{sys.version.split()[0]}")
    print(f"浏览器通道：{settings['browser_channel']}")
    print(f"输出目录：{output_root(settings)}")
    if not (output_root(settings).exists() or output_root(settings).parent.exists()):
        print("检查失败：输出目录的上级目录不存在。", file=sys.stderr)
        return 1
    from .extractor import EXTRACTOR
    if not EXTRACTOR.exists():
        print(f"检查失败：抽取脚本不存在：{EXTRACTOR}", file=sys.stderr)
        return 1
    if settings["browser_channel"] != "chromium":
        browser_candidates = [
            shutil.which(str(settings["browser_channel"])),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        if not any(browser_candidates):
            print(f"检查失败：找不到浏览器通道：{settings['browser_channel']}", file=sys.stderr)
            return 1
    if importlib.util.find_spec("playwright") is None:
        print("检查失败：缺少 Playwright，请运行 .\\scripts\\setup.ps1。", file=sys.stderr)
        return 1
    print(f"Playwright：{version('playwright')}")
    print("检查通过。")
    return 0


def command_list(_: argparse.Namespace) -> int:
    registry = load_registry()
    if not registry.get("courses"):
        print("当前没有登记课程。")
        return 0
    for name, info in sorted(registry["courses"].items()):
        output_dir = resolve_path(info["vod_output_dir"])
        stats = summarize(output_dir)
        print(f"{name}\t{info.get('teclId', '')}\t{stats['complete']}/{stats['lessons']}\t{output_dir}")
    return 0


def command_add(args: argparse.Namespace) -> int:
    registry = load_registry()
    settings = load_settings()
    name = args.name
    if name in registry.get("courses", {}) and not args.replace:
        print(f"课程已登记：{name}。需要覆盖时添加 --replace。", file=sys.stderr)
        return 1
    key = course_key(name)
    output_dir = output_root(settings) / key
    info = {
        "url": args.url,
        "course_name": name,
        "vod_output_dir": str(output_dir.resolve()),
        "teclId": "",
    }
    print(f"开始抓取：{name}")
    code = run_extractor(args.url, output_dir, profile_for(output_dir), settings, skip_existing=args.skip_existing)
    if code != 0:
        return code
    course_json = output_dir / "course.json"
    if course_json.exists():
        import json
        discovered = json.loads(course_json.read_text(encoding="utf-8"))
        info["teclId"] = str(discovered.get("teclId") or "")
        info["course_name"] = discovered.get("subjName") or name
    registry.setdefault("courses", {})[name] = info
    save_registry(registry)
    print_summary(name, output_dir)
    return 0


def get_course(args: argparse.Namespace):
    registry = load_registry()
    item = resolve_course(registry, args.course)
    if item is None:
        print(f"找不到课程：{args.course}", file=sys.stderr)
        return None
    return item


def command_fetch(args: argparse.Namespace) -> int:
    item = get_course(args)
    if item is None:
        return 1
    name, info = item
    settings = load_settings()
    output_dir = course_output_dir(info, resolve_path)
    code = run_extractor(info["url"], output_dir, profile_for(output_dir), settings, skip_existing=args.skip_existing)
    print_summary(name, output_dir)
    return code


def command_status(args: argparse.Namespace) -> int:
    item = get_course(args)
    if item is None:
        return 1
    name, info = item
    output_dir = course_output_dir(info, resolve_path)
    print(f"课程：{name}\n网址：{info.get('url', '')}\n输出目录：{output_dir}")
    print_summary(name, output_dir)
    return 0


def command_report(args: argparse.Namespace) -> int:
    item = get_course(args)
    if item is None:
        return 1
    name, info = item
    output_dir = course_output_dir(info, resolve_path)
    print_summary(name, output_dir)
    for row in sorted(lesson_rows(output_dir), key=lambda value: value["date"]):
        state = "完成" if row["complete"] else "空字幕" if row["subtitle_count"] == 0 else "待处理"
        print(f"{row['date']}\t第{row['number']}节\t{row['id']}\t{state}")
    return 0


def command_retry(args: argparse.Namespace) -> int:
    item = get_course(args)
    if item is None:
        return 1
    name, info = item
    settings = load_settings()
    output_dir = course_output_dir(info, resolve_path)
    code = run_extractor(info["url"], output_dir, profile_for(output_dir), settings, lesson_id=args.lesson_id)
    print_summary(name, output_dir)
    return code


def command_auth_clear(args: argparse.Namespace) -> int:
    item = get_course(args)
    if item is None:
        return 1
    _, info = item
    profile = profile_for(course_output_dir(info, resolve_path))
    if not profile.exists():
        print(f"认证目录不存在：{profile}")
        return 0
    import shutil
    shutil.rmtree(profile)
    print(f"已清理认证目录：{profile}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NUAA 课程字幕提取工具")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="检查运行环境")
    sub.add_parser("list", help="列出已登记课程")
    ui = sub.add_parser("ui", help="打开课程字幕管理界面")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--no-open", action="store_true")
    add = sub.add_parser("add", help="登记并抓取课程")
    add.add_argument("url")
    add.add_argument("--name", required=True)
    add.add_argument("--replace", action="store_true")
    add.add_argument("--skip-existing", action="store_true")
    for command, help_text in (("fetch", "增量抓取课程"), ("status", "查看课程状态"), ("report", "查看逐节结果"), ("auth-clear", "清理课程认证状态")):
        current = sub.add_parser(command, help=help_text)
        current.add_argument("course")
    retry = sub.add_parser("retry", help="重试单节课程")
    retry.add_argument("course")
    retry.add_argument("--lesson-id", required=True)
    fetch = sub.choices["fetch"]
    fetch.add_argument("--skip-existing", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "ui":
        from .web import serve
        return serve(args.port, not args.no_open)
    handlers = {
        "doctor": command_doctor,
        "list": command_list,
        "add": command_add,
        "fetch": command_fetch,
        "status": command_status,
        "report": command_report,
        "retry": command_retry,
        "auth-clear": command_auth_clear,
    }
    return handlers[args.command](args)
