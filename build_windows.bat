@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  NTP/NTS Diagnostic Tool - Windows Build
echo ============================================================
echo.

set "PYEXE="
set "PYARGS="
where python >nul 2>&1
if not errorlevel 1 (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 --version >nul 2>&1
        if not errorlevel 1 (
            set "PYEXE=py"
            set "PYARGS=-3"
        )
    )
)
if not defined PYEXE (
    echo ERROR: Python 3 was not found.
    pause
    exit /b 1
)

set "FINDER=%TEMP%\find_latest_ntp_nts_%RANDOM%.py"
> "%FINDER%" echo import re, sys
>>"%FINDER%" echo from pathlib import Path
>>"%FINDER%" echo root = Path(sys.argv[1])
>>"%FINDER%" echo rx = re.compile(r"^ntp_nts_tester_v(\d+)(?:_(\d+))?(?:_(\d+))?(?:_(\d+))?\.py$", re.I)
>>"%FINDER%" echo found = []
>>"%FINDER%" echo for p in root.iterdir():
>>"%FINDER%" echo     m = rx.match(p.name)
>>"%FINDER%" echo     if m:
>>"%FINDER%" echo         v = tuple(int(x or 0) for x in m.groups())
>>"%FINDER%" echo         found.append((v, p.name))
>>"%FINDER%" echo if not found: sys.exit(2)
>>"%FINDER%" echo print(max(found)[1])

set "APP_SOURCE="
for /f "usebackq delims=" %%F in (`%PYEXE% %PYARGS% "%FINDER%" "%CD%"`) do set "APP_SOURCE=%%F"
del /q "%FINDER%" >nul 2>&1

if not defined APP_SOURCE (
    echo ERROR: No versioned application source was found.
    pause
    exit /b 1
)
if not exist "%APP_SOURCE%" (
    echo ERROR: Selected source does not exist: %APP_SOURCE%
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo ERROR: requirements.txt was not found.
    pause
    exit /b 1
)

echo Selected latest source:
echo   %APP_SOURCE%
echo.

if exist ".venv" rmdir /s /q ".venv"
%PYEXE% %PYARGS% -m venv ".venv"
if errorlevel 1 goto :fail

set "VPY=%CD%\.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
"%VPY%" -m pip install -r "requirements.txt"
if errorlevel 1 goto :fail
"%VPY%" -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

"%VPY%" -m PyInstaller --noconfirm --clean --onefile --windowed --name "NTP-NTS-Diagnostic-Tool" "%APP_SOURCE%"
if errorlevel 1 goto :fail

if not exist "dist\NTP-NTS-Diagnostic-Tool.exe" goto :fail

echo.
echo ============================================================
echo  BUILD SUCCESSFUL
echo ============================================================
echo Source:
echo   %APP_SOURCE%
echo Output:
echo   %CD%\dist\NTP-NTS-Diagnostic-Tool.exe
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  BUILD FAILED
echo ============================================================
if defined APP_SOURCE (echo Source selected: %APP_SOURCE%) else (echo Source selected: [none])
pause
exit /b 1
