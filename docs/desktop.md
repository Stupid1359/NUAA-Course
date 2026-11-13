# 课程字幕桌面应用

在源码目录执行 `powershell -ExecutionPolicy Bypass -File scripts/build-desktop.ps1` 后，打开同级 `app/课程字幕.exe`。运行电脑需要 Microsoft Edge 和 WebView2 Runtime。

选择课程和课次后启动抓取，在 Edge 中完成学校登录。执行记录支持复制、下载和终止操作。关闭应用窗口会结束当前任务和相关浏览器进程。

## 文件位置

以下路径相对于工作区根目录。

| 路径 | 内容 |
| --- | --- |
| `app/课程字幕.exe` | 桌面入口 |
| `app/nuaa-course-worker.exe` | 抓取组件 |
| `app/_internal` | 运行依赖 |
| `data/courses` | 课程、字幕和登录资料 |
| `data/courses.local.json` | 当前课程登记 |
| `data/courses.json` | 已保留的课程登记资料 |
| `data/settings.local.json` | 应用配置 |
| `data/webview` | 桌面显示设置 |
| `data/logs` | 应用日志 |

桌面与浏览器界面共用 `data`，相对课程目录以 `data` 为起点。更新程序时保留 `data`；迁移电脑时一起复制 `app`、`data` 和启动脚本。登录资料和课程网址包含个人认证信息，请自行保管。

在 `NUAA-Course` 执行 `powershell -ExecutionPolicy Bypass -File scripts/build-desktop.ps1`。构建中间文件位于 `.cache`，生成程序复制到相邻的 `app`。
