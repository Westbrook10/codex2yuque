@echo off
chcp 65001 >nul
title Codex to Yuque Converter
set PYTHONUTF8=1
where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0codex2yuque.py" --clip
) else (
  py "%~dp0codex2yuque.py" --clip
)
echo.
pause
