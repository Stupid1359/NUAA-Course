from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, render_template, request
from werkzeug.serving import make_server

from .config import PACKAGE_ROOT, load_registry, load_settings, output_root, resolve_path, save_registry
from .extractor import extractor_command
from .inventory import lesson_rows


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def discover_courses() -> dict[str, dict]:
    courses = {}
    for directory in sorted(output_root(load_settings()).glob("*")):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        info = read_json(directory / "course.json")
        if not info and not (directory / "replay_inventory.json").exists():
            continue
        courses[directory.name] = {
            "key": directory.name,
            "name": info.get("subjName") or directory.name,
            "teclId": str(info.get("teclId") or ""),
            "teachers": info.get("teacNames") or [],
            "directory": directory.resolve(),
            "url": read_json(directory / "raw" / "page.json").get("url", ""),
        }
    for name, info in load_registry().get("courses", {}).items():
        directory = resolve_path(info["vod_output_dir"]).resolve()
        existing = next((c for c in courses.values() if
                         c["directory"] == directory or
                         (info.get("teclId") and c["teclId"] == str(info["teclId"])) or
                         c["name"] == name), None)
        if existing:
            if not existing["url"]:
                existing["url"] = info.get("url", "")
            continue
        key = directory.name
        if key in courses:
            key = str(info.get("teclId") or name)
        courses[key] = {
            "key": key, "name": name, "teclId": str(info.get("teclId") or ""),
            "teachers": [], "directory": directory, "url": info.get("url", ""),
        }
    return courses


def course_details(course: dict) -> dict:
    rows = lesson_rows(course["directory"])
    for row in rows:
        if row["complete"]:
            row["state"] = "complete"
        elif row["subtitle_file"] and row["subtitle_count"] == 0:
            row["state"] = "empty"
        else:
            row["state"] = "pending"
    rows.sort(key=lambda row: row["date"])
    return {
        **{key: value for key, value in course.items() if key != "directory"},
        "output_dir": str(course["directory"]),
        "lessons": rows,
        "counts": {
            "total": len(rows),
            "complete": sum(row["state"] == "complete" for row in rows),
            "empty": sum(row["state"] == "empty" for row in rows),
            "pending": sum(row["state"] == "pending" for row in rows),
        },
    }


def build_command(course: dict, lesson_ids: list[str], inventory_only: bool,
                  skip_existing: bool, wait: int) -> list[str]:
    settings = load_settings()
    directory = course["directory"]
    # 复用已成功登录的课程浏览器目录。
    edge_profile = directory / ".edge-profile"
    profile = edge_profile if edge_profile.is_dir() else directory / ".browser-profile"
    command = [
        *extractor_command(), course["url"],
        "--output-dir", str(directory), "--browser-runtime-auth",
        "--browser-channel", settings["browser_channel"],
        "--user-data-dir", str(profile), "--manual-wait-seconds", str(wait),
        "--timeout-ms", str(settings["timeout_ms"]),
        "--extra-wait-ms", str(settings["extra_wait_ms"]), "--batch",
    ]
    if inventory_only:
        command.append("--inventory-only")
    else:
        command.extend(["--lesson-ids", *lesson_ids])
    if skip_existing:
        command.append("--skip-existing")
    return command


class JobManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.job = None
        self.process = None
        self.stopping = False
        self.cancel_requested = False
        self.worker = None
        records = [
            course["directory"] / "ui-run.json"
            for course in discover_courses().values()
            if (course["directory"] / "ui-run.json").is_file()
        ]
        if records:
            latest = max(records, key=lambda path: path.stat().st_mtime_ns)
            self.job = read_json(latest)
            if self.job["state"] in {"running", "cancelling"}:
                self.job["state"] = "cancelled"
                self.job["ended_at"] = datetime.now().isoformat(timespec="seconds")
                self.job["logs"].append("程序已经结束，任务已终止。")

    def snapshot(self):
        with self.lock:
            if self.job is None:
                return None
            return {**self.job, "logs": list(self.job["logs"])}

    def start(self, course, lesson_ids, inventory_only, skip_existing, wait):
        command = build_command(course, lesson_ids, inventory_only, skip_existing, wait)
        with self.lock:
            if self.stopping or (self.worker and self.worker.is_alive()):
                return False
            self.cancel_requested = False
            self.job = {
                "id": secrets.token_hex(8), "course": course["key"],
                "course_name": course["name"], "state": "running",
                "mode": "inventory" if inventory_only else "extract",
                "selected": lesson_ids, "started_at": datetime.now().isoformat(timespec="seconds"),
                "ended_at": None, "exit_code": None, "logs": [],
            }
            self.worker = threading.Thread(target=self.run, args=(command, course), daemon=True)
            self.worker.start()
        return True

    def stop(self):
        with self.lock:
            self.stopping = True
        self.cancel()

    def cancel(self, job_id=None):
        with self.lock:
            if not self.job or (job_id is not None and self.job["id"] != job_id):
                return False
            if self.job["state"] not in {"running", "cancelling"}:
                return True
            self.cancel_requested = True
            self.job["state"] = "cancelling"
            process = self.process
            worker = self.worker
        if process and process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.terminate()
        if worker:
            worker.join(timeout=10)
        return True

    def run(self, command, course):
        environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
        try:
            with self.lock:
                process = None
                if not self.cancel_requested:
                    process = subprocess.Popen(
                        command, cwd=PACKAGE_ROOT, env=environment, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    self.process = process
            for line in process.stdout if process else ():
                # 日志中隐藏课程网址携带的认证参数。
                line = re.sub(r"https?://[^\s]+", "[课程网址]", line.rstrip())
                with self.lock:
                    self.job["logs"].append(line)
            code = process.wait() if process else None
            if process:
                process.stdout.close()
            with self.lock:
                self.job["exit_code"] = code
                self.job["state"] = "cancelled" if self.cancel_requested else ("success" if code == 0 else "failed")
                if self.cancel_requested:
                    self.job["logs"].append("操作已终止，已保存的字幕可以继续使用。")
                self.job["ended_at"] = datetime.now().isoformat(timespec="seconds")
        except Exception as exc:
            # 后台任务的异常转换成可见失败状态，并终止当前任务。
            with self.lock:
                self.job["state"] = "cancelled" if self.cancel_requested else "failed"
                self.job["logs"].append(f"{type(exc).__name__}: {exc}")
                self.job["ended_at"] = datetime.now().isoformat(timespec="seconds")
        snapshot = self.snapshot()
        course["directory"].mkdir(parents=True, exist_ok=True)
        (course["directory"] / "ui-run.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        with self.lock:
            self.process = None


class PageLifecycle:
    def __init__(self, shutdown):
        self.shutdown = shutdown
        self.lock = threading.Lock()
        self.pages = {}
        self.seen = False
        self.empty_since = None
        self.finished = threading.Event()

    def update(self, page_id, closed=False):
        with self.lock:
            self.seen = True
            if closed:
                self.pages.pop(page_id, None)
            else:
                self.pages[page_id] = time.monotonic()
            self.empty_since = None

    def watch(self):
        while not self.finished.wait(0.5):
            with self.lock:
                now = time.monotonic()
                self.pages = {key: stamp for key, stamp in self.pages.items() if now - stamp < 45}
                if self.seen and not self.pages:
                    if self.empty_since is None:
                        self.empty_since = now
                    if now - self.empty_since >= 4:
                        break
                else:
                    self.empty_since = None
        if not self.finished.is_set():
            self.shutdown()


def create_app(lifecycle=None) -> Flask:
    app = Flask(__name__)
    token = secrets.token_hex(32)
    manager = JobManager()
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.extensions["jobs"] = manager

    @app.before_request
    def local_requests():
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            abort(403)
        if request.host.split(":")[0] not in {"127.0.0.1", "localhost"}:
            abort(403)
        supplied_token = request.headers.get("X-Local-Token")
        if request.path == "/api/page" and request.is_json:
            supplied_token = (request.get_json(silent=True) or {}).get("token")
        if request.method == "POST" and supplied_token != token:
            abort(403)

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'"
        )
        return response

    def find_course(key):
        course = discover_courses().get(key)
        if course is None:
            abort(404, description="找不到课程")
        return course

    @app.get("/")
    def index():
        return render_template("index.html", token=token)

    @app.post("/api/page")
    def page_presence():
        body = request.get_json()
        page_id = body.get("page_id")
        if not isinstance(page_id, str) or not 1 <= len(page_id) <= 100:
            abort(400)
        if lifecycle:
            lifecycle.update(page_id, body.get("closed") is True)
        return jsonify({"ok": True})

    @app.get("/api/courses")
    def courses():
        return jsonify([course_details(course) for course in discover_courses().values()])

    @app.get("/api/job")
    def job():
        return jsonify(manager.snapshot())

    @app.post("/api/course")
    def save_course():
        body = request.get_json()
        if manager.snapshot() and manager.snapshot()["state"] in {"running", "cancelling"}:
            abort(409, description="请等待当前任务完成后修改课程")
        name = str(body.get("name", "")).strip()
        url = str(body.get("url", "")).strip()
        parsed = urlparse(url)
        if not name or len(name) > 100:
            abort(400, description="请输入不超过 100 个字符的课程名称")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or not (
            parsed.hostname == "nuaa.edu.cn" or parsed.hostname.endswith(".nuaa.edu.cn")
        ):
            abort(400, description="请输入完整的南航课程网址")
        existing = discover_courses().get(body.get("key"))
        if existing:
            directory = existing["directory"]
            name = existing["name"]
        else:
            key = re.sub(r'[^\w.-]+', "_", name, flags=re.UNICODE).strip("._")
            if not key:
                abort(400, description="课程名称需要包含文字或数字")
            directory = output_root(load_settings()) / key
            if directory.exists():
                abort(409, description="该课程目录已经存在，请选择课程后更新网址")
        registry = load_registry()
        registry["courses"][name] = {
            "url": url, "course_name": name, "vod_output_dir": str(directory),
            "teclId": existing["teclId"] if existing else "",
        }
        if existing:
            page_path = directory / "raw" / "page.json"
            page = read_json(page_path)
            page["url"] = url
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
        save_registry(registry)
        return jsonify({"key": existing["key"] if existing else directory.name})

    @app.post("/api/job")
    def start_job():
        body = request.get_json()
        course = find_course(body.get("course"))
        if not course["url"]:
            abort(400, description="请为课程填写完整网址")
        selected = body.get("lesson_ids", [])
        if not isinstance(selected, list) or any(not isinstance(item, str) for item in selected):
            abort(400, description="课次编号格式错误")
        selected = list(dict.fromkeys(selected))
        inventory_only = body.get("inventory_only") is True
        valid = {row["id"] for row in lesson_rows(course["directory"])}
        if not inventory_only and (not selected or not set(selected) <= valid):
            abort(400, description="请勾选当前课程中的有效课次")
        wait = body.get("wait", 120)
        if type(wait) is not int or not 0 <= wait <= 600:
            abort(400, description="登录等待时间需要在 0 到 600 秒之间")
        if not manager.start(course, selected, inventory_only, body.get("skip_existing") is True, wait):
            abort(409, description="已有抓取任务运行，请等待完成")
        return jsonify(manager.snapshot()), 202

    @app.post("/api/job/cancel")
    def cancel_job():
        body = request.get_json()
        if not isinstance(body.get("id"), str):
            abort(400, description="请提供任务编号")
        if not manager.cancel(body["id"]):
            abort(409, description="任务已经更新，请刷新执行记录")
        return jsonify(manager.snapshot())

    @app.get("/api/transcript")
    def transcript():
        course = find_course(request.args.get("course"))
        lesson_id = request.args.get("lesson", "")
        if lesson_id not in {row["id"] for row in lesson_rows(course["directory"])}:
            abort(404)
        path = course["directory"] / "lessons" / lesson_id / "raw" / "transcript.txt"
        if not path.is_file():
            abort(404, description="当前课次没有字幕文本")
        return app.response_class(path.read_text(encoding="utf-8"), mimetype="text/plain")

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def api_error(error):
        return jsonify({"error": error.description}), error.code

    return app


def serve(port: int = 8765, open_browser: bool = True) -> int:
    lifecycle = PageLifecycle(lambda: server.shutdown())
    app = create_app(lifecycle)
    server = make_server("127.0.0.1", port, app, threaded=True)
    watcher = threading.Thread(target=lifecycle.watch, daemon=True)
    watcher.start()
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"课程字幕管理界面：{url}", flush=True)
    print("关闭最后一个管理页面后，程序和抓取任务会自动结束。", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        lifecycle.finished.set()
        app.extensions["jobs"].stop()
        server.server_close()
    return 0
