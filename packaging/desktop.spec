from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH).parent
analysis = Analysis(
    [str(project_root / "packaging/desktop_entry.py")],
    pathex=[str(project_root)],
    binaries=[(str(path), ".") for path in (Path(sys.base_prefix) / "Library/bin").glob("ffi*.dll")],
    datas=[
        *collect_data_files("nuaa_course"),
        (str(project_root / "skills/nuaa-vod-summarizer/scripts/extract_nuaa_vod.py"),
         "skills/nuaa-vod-summarizer/scripts"),
    ],
    hiddenimports=["webview.platforms.edgechromium", "webview.platforms.winforms"],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "pytest"],
)
archive = PYZ(analysis.pure)
app = EXE(
    archive, analysis.scripts, [], exclude_binaries=True,
    name="课程字幕", console=False,
)
worker = EXE(
    archive, analysis.scripts, [], exclude_binaries=True,
    name="nuaa-course-worker", console=True,
)
COLLECT(app, worker, analysis.binaries, analysis.datas, name="课程字幕")
