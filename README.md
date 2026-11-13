# NUAA-Course

南航课程字幕管理应用，支持课程登记、课次选择、字幕抓取、字幕预览和执行记录。

源码目录可发布到自己的 GitHub 仓库。运行资料保存在同级的 `data` 目录，桌面程序构建到同级的 `app` 目录。安装后可运行 `scripts/open-web.cmd`；构建桌面程序后可打开 `../app/课程字幕.exe`。抓取课程时在 Edge 中完成学校登录。

## 目录

| 目录 | 内容 |
| --- | --- |
| `../app` | 桌面程序及运行依赖 |
| `../data/courses` | 课程清单、字幕、浏览器登录资料 |
| `../data` | 课程登记、配置、日志和界面设置 |
| `nuaa_course` | Python package 和网页界面 |
| `skills` | 字幕抓取、字幕转讲义和 Obsidian 工具 |
| `scripts` | 安装、启动、构建脚本 |
| `packaging` | PyInstaller 配置和桌面入口 |
| `examples` | 配置示例 |
| `docs` | 使用说明和架构文档 |
| `course_materials` | 计算机网络与编译原理Ⅰ的讲义、复习资料、作业考试资料和带时间字幕 |
| `.cache` | 构建、测试和迁移校验文件 |

源码目录为 `NUAA-Course`，发行包名称为 `nuaa-course`，Python package 为 `nuaa_course`。

## 开发与使用

在源码目录执行 `scripts/setup.ps1` 安装依赖。运行 `scripts/nuaa-course.ps1 doctor` 检查环境，运行 `scripts/open-web.cmd` 打开浏览器界面。

构建桌面应用：`powershell -ExecutionPolicy Bypass -File scripts/build-desktop.ps1`。

参阅 [安装说明](docs/installation.md)、[桌面说明](docs/desktop.md)、[架构说明](docs/architecture.md)、[GitHub 发布说明](docs/github.md)。

## 字幕转讲义

[nuaa-course-note](skills/nuaa-course-note/SKILL.md) 根据指定课程的带时间字幕生成逐课次讲义，并维护作业、考试与成绩事项及章节索引。该 skill 的完整文件位于 `skills/nuaa-course-note/`，源资料与输出目录按使用时的请求确定。
