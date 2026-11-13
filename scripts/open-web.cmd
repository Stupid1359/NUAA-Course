@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m nuaa_course ui
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\nuaa-course.ps1" ui
)
