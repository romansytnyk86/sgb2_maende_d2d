@echo off
REM ============================================================
REM  SGB II MaEnde - Deployment Launcher
REM  Replaces: BAT_SGB_II_MaEnde_D2D.BAT
REM            BAT_SGB_II_MaEnde_D2D_ohne_PD.BAT
REM ============================================================

if "%1"=="" goto usage
if "%1"=="ohne-backup" goto ohne
if "%1"=="mit-backup"  goto mit
goto usage

:ohne
echo Running: ohne-backup workflow
python main.py ohne-backup
goto end

:mit
if "%2"=="" (
    set /p "MONTH=Bitte Monat fuer das Backup-Projekt angeben (z.B. 202512): "
) else (
    set MONTH=%2
)
echo Running: mit-backup workflow [backup-month: %MONTH%]
python main.py mit-backup --backup-month %MONTH%
goto end

:usage
echo.
echo Usage:
echo   run.bat ohne-backup
echo   run.bat mit-backup [YYYYMM]
echo.
echo Examples:
echo   run.bat ohne-backup
echo   run.bat mit-backup 202512
echo.

:end
