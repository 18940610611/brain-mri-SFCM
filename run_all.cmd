@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [1/6] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)

set "PY=.venv\Scripts\python.exe"
echo [2/6] Installing dependencies...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/6] Running implementation sanity check...
"%PY%" run_sanity.py
if errorlevel 1 goto :error

echo [4/6] Checking BrainWeb files...
"%PY%" run_brainweb.py --check-only
if errorlevel 1 (
  echo.
  echo Put the seven BrainWeb files under data\brainweb according to README.md, then run this file again.
  goto :error
)

echo [5/6] Running formal noise and RF experiments...
"%PY%" run_brainweb.py --suite noise --axis 2 --slices 70 80 90 100 110 --repeats 5
if errorlevel 1 goto :error
"%PY%" run_brainweb.py --suite rf --axis 2 --slices 70 80 90 100 110 --repeats 5
if errorlevel 1 goto :error

echo [6/6] Running parameter sensitivity experiment...
"%PY%" run_brainweb.py --suite params --image data\brainweb\t1_icbm_normal_1mm_pn5_rf20.rawb.gz --label data\brainweb\phantom_1.0mm_normal_crisp.rawb.gz --axis 2 --slice 90
if errorlevel 1 goto :error

echo.
echo Finished. See results\noise, results\rf, and results\params.
exit /b 0

:error
echo.
echo Experiment stopped. Check the message above and README.md.
exit /b 1
