@echo off
chcp 65001 >nul
title Convert MD for MarkText
set PYTHONUTF8=1
if "%~1"=="" (
  echo Please drag a .md file onto this .bat icon.
  pause
  exit /b 1
)
where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0codex2yuque.py" "%~1" -m import -o "%~1"
) else (
  py "%~dp0codex2yuque.py" "%~1" -m import -o "%~1"
)
echo.
echo [DONE] Converted LaTeX delimiters to $$...$$ for MarkText.
pause
