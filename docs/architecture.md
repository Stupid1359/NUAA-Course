# NUAA-Course 架构

源码目录为 `NUAA-Course`。桌面程序和用户资料分别保存在源码目录同级的 `app`、`data`。

`nuaa_course/config.py` 管理配置与路径，`cli.py` 提供命令入口，`desktop.py` 管理 WebView2 窗口，`web.py` 管理本机 API 和任务进程。`inventory.py` 读取课次状态，`extractor.py` 组织抓取命令。界面位于 `templates` 和 `static`，平台抓取与 Obsidian 工具位于 `skills`。

开发模式和桌面模式共用工作区中的 `data`。`NUAA_COURSE_DATA_DIR` 可以指定独立资料目录，测试使用 `.cache/tests`。`output_root` 默认为 `courses`，相对路径以 `data` 为起点。

一次执行一个任务。开发模式启动 Python 脚本，桌面模式启动 `nuaa-course-worker.exe`。终止操作结束任务及其子进程并保存结果。关闭桌面窗口会清理当前任务。

`packaging` 保存构建配置，`scripts` 保存安装和构建入口，`.cache` 保存构建与测试文件。
