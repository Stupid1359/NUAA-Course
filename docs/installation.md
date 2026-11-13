# 安装说明

## 环境要求

- Windows
- Python 3.10 或更高版本
- Microsoft Edge
- 南航统一认证账号

## 安装步骤

将仓库克隆到工作区的 `NUAA-Course` 目录。在仓库目录打开 PowerShell，执行：

```powershell
.\scripts\setup.ps1
```

脚本会完成以下操作：

- 创建项目虚拟环境 `.venv`。
- 安装 `nuaa-course` 命令和 Playwright。
- 安装 Playwright Chromium 运行文件。
- 创建并检查课程输出目录。

## 检查环境

```powershell
.\scripts\nuaa-course.ps1 doctor
```

显示“检查通过”后即可抓取课程。

## 打开可视化界面

浏览器界面可以通过 `scripts/open-web.cmd` 打开，也可以执行：

```powershell
.\scripts\nuaa-course.ps1 ui
```

在左侧选择课程，勾选课次，然后点击“抓取所选课次”。第一次添加课程后，需要点击“更新课次清单”，在 Edge 中完成登录并等待读取结束。

## 抓取课程

```powershell
.\scripts\nuaa-course.ps1 add "课程完整网址" --name "课程名称"
```

课程网址需要从已经能够打开的课程页面复制完整地址。程序打开 Edge 后，完成统一认证并等待课程页面加载。

## 再次抓取

```powershell
.\scripts\nuaa-course.ps1 fetch "课程名称" --skip-existing
```

程序会跳过同时存在 `subtitle.json` 和 `transcript.txt` 的课次，并重新请求缺少完整文件的课次。

## 排查结果

```powershell
.\scripts\nuaa-course.ps1 status "课程名称"
.\scripts\nuaa-course.ps1 report "课程名称"
```

逐节结果会区分已经完成、空字幕和待处理课次。

认证状态异常时执行：

```powershell
.\scripts\nuaa-course.ps1 auth-clear "课程名称"
```

随后重新执行 `fetch`，在浏览器中完成认证。
