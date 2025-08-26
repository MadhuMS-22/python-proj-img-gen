@echo off
setlocal

REM --- Change to script directory
cd /d "%~dp0"

if not exist ".venv" (
  py -3 -m venv .venv
)

call .venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel

REM Install TensorFlow CPU version first for compatibility
echo Installing TensorFlow CPU for compatibility...
pip uninstall tensorflow tensorflow-cpu -y >nul 2>&1
pip install tensorflow-cpu==2.16.1 opencv-python==4.8.1.78 numpy==1.26.4

REM Install project requirements if present
if exist requirements.txt (
  pip install -r requirements.txt
) else (
  echo requirements.txt not found — continuing.
)

REM Ensure PyTorch CPU is present
python - <<PY
import importlib, sys, subprocess
def has(mod):
    try:
        importlib.import_module(mod); print(f"FOUND {mod}"); return True
    except Exception as e:
        print(f"MISSING {mod}: {e}"); return False
need_torch = not has("torch")
if need_torch:
    print("Installing CPU-only PyTorch...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"])
PY

REM Try to install Real-ESRGAN runtime (for inference)
pip install realesrgan basicsr

echo Setup complete.
echo Use: .venv\Scripts\python.exe RUN_FIRST.py
exit /b 0
