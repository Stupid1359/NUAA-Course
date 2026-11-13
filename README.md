# NUAA-Course

## 准备环境

需要 Windows、Python 3.10 或更高版本、Microsoft Edge，以及能够登录南航飞天云课堂的账号。以下命令在 PowerShell 中执行。`setup.ps1` 会安装 Python 依赖和 Playwright Chromium，抓取课程时使用 Edge 打开登录页面。

将仓库放在一个工作目录中，例如 `E:\NUAACourses\NUAA-Course`。程序会把个人课程资料写入仓库同级的 `data` 目录。保持仓库目录与 `data` 目录的相对位置，后续查找字幕会更方便。

```powershell
git clone https://github.com/Stupid1359/NUAA-Course.git
cd NUAA-Course
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

安装结束时应显示“检查通过”。以后可以在仓库目录重新检查环境：

```powershell
.\.venv\Scripts\python.exe -m nuaa_course doctor
```

## 抓取字幕

### 通过浏览器界面操作

1. 在南航飞天云课堂打开目标课程的点播页面，复制浏览器地址栏中的完整网址。课程播放详情页和 `play-center` 页面均受支持；网址中带有较长参数时，也请完整复制。
2. 在仓库目录执行 `.\scripts\open-web.cmd`。浏览器会打开本机的课程字幕管理界面。运行期间保留启动它的命令窗口；关闭最后一个管理页面会结束程序和正在进行的任务。
3. 点击左侧“我的课程”旁的“＋”，填写便于识别的课程名称并粘贴课程完整网址，然后点击“保存课程”。课程名称用于本机目录和列表显示。
4. 进入课程页面，点击“更新课次清单”。程序会打开 Edge；首次运行时在 Edge 中完成学校登录，并进入课程页面。等待界面中的执行状态变为“已完成”，再查看课次列表。登录所需时间可以在“登录等待”处调整。
5. 勾选需要的课次，点击“抓取所选课次”。整门课程可以使用“全选”；后续补充资料可以使用“选择未完成”，并保持“跳过已有字幕”处于勾选状态。
6. 等待执行状态变为“已完成”，检查“已有字幕”“接口暂无字幕”“待抓取”的数量。点击课次右侧的“查看字幕”可以预览文本；“执行记录”可以复制或下载，便于定位失败的课次。

```powershell
.\scripts\open-web.cmd
```

“更新课次清单”只读取课次信息。勾选课次并点击“抓取所选课次”后，程序才会请求这些课次的字幕。学校平台尚未提供字幕的课次会显示“接口暂无字幕”。

### 通过命令行操作

在仓库目录运行以下命令。`add` 会登记课程并抓取该课程的课次；`fetch` 用于再次抓取，`--skip-existing` 会跳过已经保存完整字幕的课次。

```powershell
.\.venv\Scripts\python.exe -m nuaa_course add "<课程完整网址>" --name "计算机网络"
.\.venv\Scripts\python.exe -m nuaa_course fetch "计算机网络" --skip-existing
.\.venv\Scripts\python.exe -m nuaa_course report "计算机网络"
```

`report` 会列出日期、节次、`lesson_id` 和逐节状态。只需重新请求某一节时，使用报告中的 `lesson_id`：

```powershell
.\.venv\Scripts\python.exe -m nuaa_course retry "计算机网络" --lesson-id <lesson_id>
```

### 字幕保存位置

浏览器界面会显示当前课程的“保存位置”。默认目录为仓库同级的 `data/courses/<课程目录名>/`，其中每节课的资料位于 `lessons/<lesson_id>/`：

| 文件 | 内容 |
| --- | --- |
| `metadata.json` | 课程、日期、节次和课次编号等信息 |
| `raw/transcript.txt` | 带时间信息的字幕文本，供阅读和编写讲义 |
| `raw/subtitle.json` | 平台返回的字幕条目，供核对原始文字和时间 |

课程目录中的 `replay_inventory.json` 保存课次清单，`course.json` 保存课程信息。`data` 目录还可能包含登录资料和平台响应，请自行保管。仓库内的 `course_materials/` 是已检查的公开课程资料，供浏览和参考；新抓取的资料保存在同级的 `data` 目录。

## 将字幕整理为讲义

网页界面提供字幕抓取与预览。编写逐课次讲义时，让能够读取本地文件的 AI 助手使用 [nuaa-course-note](skills/nuaa-course-note/SKILL.md) 及其 `references/` 中的规则。该 skill 会要求核对完整字幕和时间信息，并维护课程的作业、考试与章节索引。

1. 先使用 `report` 找到目标课次的 `lesson_id`，确认该节显示“完成”；再检查对应的 `raw/transcript.txt` 确实有课堂内容和时间信息。
2. 在 AI 工具中打开同时包含 `NUAA-Course` 与 `data` 的工作目录，并允许它读取课程资料。讲义建议写入同级的 `课程/<课程名称>/`；也可以在请求中指定自己的目标目录。
3. 将下方请求中的课程名称、资料目录、课次编号和目标目录替换为实际值。资料目录以浏览器界面显示的“保存位置”为准。
4. 阅读生成的讲义，核对主题时间、教师原话、作业要求和章节位置。字幕文字含有识别错误或资料缺口时，根据课堂视频或课件补充核对。

```text
请读取 NUAA-Course/skills/nuaa-course-note/SKILL.md 及其中引用的 references。
课程：计算机网络
源资料目录：data/courses/计算机网络
目标课次：<lesson_id>，对应日期和节次请核对 metadata.json
讲义目标目录：课程/计算机网络

请完整阅读该课次的 metadata.json、raw/transcript.txt 和 raw/subtitle.json。
按 skill 的规则生成带时间范围的逐课次讲义；同步维护
作业&考试/作业.md、作业&考试/考试.md 和复习/章节索引.md。
保留已核实事项的来源时间与教师原话，标明资料缺口，不补写没有来源的课堂内容。
```

默认的讲义文件名为 `YYYY-MM-DD 第N节.md`。完成后，目标课程目录应包含 `讲义/`、`作业&考试/` 和 `复习/`；逐节讲义与事项文件、章节索引之间使用相对链接。继续整理同一课程时，指定新的 `lesson_id` 和相同的目标目录，AI 助手会根据已有文件继续维护。

需要公开讲义时，检查学生姓名、联系方式、账号凭据、本机路径等信息。含个人信息的课堂引文按 skill 中的公开规则处理。`data` 中的浏览器登录资料与平台响应不要上传到公开仓库。

## 常见问题

- **安装或检查环境失败：**确认 `py -3 --version` 能显示 Python 3.10 或更高版本，并确认已安装 Edge；随后重新运行 `setup.ps1` 和 `doctor`。
- **课次列表为空：**确认添加的是能够在浏览器中打开的完整课程网址，在 Edge 完成登录后重新点击“更新课次清单”。
- **字幕显示“接口暂无字幕”：**该节的字幕接口当前没有返回内容。可以稍后重试；生成讲义需要有课堂内容和可靠时间信息。
- **登录状态异常：**在界面中查看执行记录；命令行可以执行下方的 `auth-clear`，随后重新抓取并在 Edge 登录。该命令会清理这门课程保存的浏览器认证状态。
- **不知道讲义应读取哪个目录：**查看界面中的“保存位置”，或运行 `report` 确认 `lesson_id`，再进入对应的 `lessons/<lesson_id>/raw/`。

```powershell
.\.venv\Scripts\python.exe -m nuaa_course auth-clear "计算机网络"
```

更多资料：[安装说明](docs/installation.md)、[桌面应用](docs/desktop.md)、[项目结构](docs/architecture.md)、[GitHub 发布说明](docs/github.md)。
