# GitHub 发布说明

在 `NUAA-Course` 目录执行 Git 命令。发布时使用自己创建的 GitHub 仓库地址，并确认所登录账号具有写入权限。

仓库包含 Python 源码、网页界面、脚本、示例配置、通用文档，以及 `course_materials/计算机网络` 和 `course_materials/编译原理Ⅰ` 中的课程资料。两门课程的讲义、复习资料、作业考试资料和带时间字幕经过隐私处理后收录。工作区同级的 `data/` 保存课程网址、浏览器登录资料、原始字幕、平台响应和日志；`app/` 保存本机生成的程序；`课程/` 保存原始课程资料。电影史论及其他课程不收录。`tests/` 和 `docs/extraction-record.md` 包含本机课程检查与抓取记录，已由忽略规则排除。

公开字幕保留课程正文中的时间范围，课堂点名内容已省略，课堂提问中出现的姓名已匿名处理。公开讲义中的 `source` 指向仓库内的字幕文件。发布前检查新加入的资料中是否出现学生姓名、联系方式、账号凭据、本机路径等信息。

`skills/nuaa-course-note/` 包含字幕转讲义的 skill、配置与参考文档。仓库副本使用可配置的资料位置，并包含公开资料的隐私处理要求。

当前使用方式为克隆仓库后执行 `scripts/setup.ps1`。字幕抓取需要仓库中的 `skills/nuaa-vod-summarizer/scripts/extract_nuaa_vod.py`；当前 wheel 未包含该脚本，单独安装 wheel 无法完成字幕抓取。

上传前，在源码目录执行：

```powershell
git status --short
git add --dry-run -A
git status --short
```

逐项确认将要暂存的文件。检查 `course_materials` 中的公开内容，并确认浏览器资料、平台响应、原始抓取目录和其他课程资料未进入待上传范围。确认后再暂存、提交，并将自己的仓库地址设为远程地址后推送。

克隆后的目录结构需要让 `NUAA-Course` 位于工作区内；`scripts/setup.ps1` 会在同级工作区创建 `data/courses`。桌面构建脚本会把程序复制到同级的 `app`。
