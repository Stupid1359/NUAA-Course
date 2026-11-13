from __future__ import annotations

import argparse
import logging
import runpy
import sys
import threading

from .config import DATA_ROOT
from .extractor import EXTRACTOR


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-worker":
        sys.argv = [str(EXTRACTOR), *sys.argv[2:]]
        # 显式导入依赖，供 PyInstaller 收集 Playwright 和浏览器驱动。
        import playwright.async_api

        runpy.run_path(str(EXTRACTOR), run_name="__main__")
        return 0

    import webview
    from werkzeug.serving import make_server

    from .web import create_app

    parser = argparse.ArgumentParser(description="课程字幕桌面应用")
    parser.add_argument("--debug-port", type=int)
    args = parser.parse_args()
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    logs_dir = DATA_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    logging.basicConfig(filename=logs_dir / "desktop.log", encoding="utf-8", level=logging.INFO)
    app = create_app()
    # 使用固定端口保存 WebView2 的 localStorage，多个应用实例通过端口互斥。
    server = make_server("127.0.0.1", 18765, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    webview.settings["ALLOW_DOWNLOADS"] = True
    if args.debug_port is not None:
        webview.settings["REMOTE_DEBUGGING_PORT"] = args.debug_port
    window = webview.create_window(
        "课程字幕 · NUAA", f"http://127.0.0.1:{server.server_port}",
        width=1440, height=960, min_size=(800, 600),
        text_select=True, zoomable=True, background_color="#f5f7f6",
    )
    window.events.closed += app.extensions["jobs"].stop
    try:
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(DATA_ROOT / "webview"))
    finally:
        app.extensions["jobs"].stop()
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
