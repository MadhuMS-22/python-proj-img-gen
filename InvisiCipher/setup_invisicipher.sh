#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel

# Install TensorFlow CPU version first for compatibility
echo "Installing TensorFlow CPU for compatibility..."
pip uninstall tensorflow tensorflow-cpu -y >/dev/null 2>&1 || true
pip install tensorflow-cpu==2.16.1 opencv-python==4.8.1.78 numpy==1.26.4

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "requirements.txt not found — continuing."
fi

python - <<'PY'
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

pip install realesrgan basicsr

echo "Setup complete."
echo "Run: ./.venv/bin/python RUN_FIRST.py"
