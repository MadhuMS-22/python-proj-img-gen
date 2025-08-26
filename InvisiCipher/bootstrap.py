#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"


def run(cmd, check=True):
    print("$", " ".join(cmd))
    return subprocess.check_call(cmd) if check else subprocess.call(cmd)


def ensure_venv():
    if not VENV_DIR.exists():
        print("[+] Creating virtual environment at .venv")
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))
    else:
        print("[=] Using existing .venv")


def venv_python():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def install_requirements():
    py = venv_python()
    run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    
    # Handle TensorFlow installation carefully
    print("[+] Installing TensorFlow CPU version for compatibility...")
    try:
        # Uninstall any existing tensorflow to avoid conflicts
        subprocess.call([py, "-m", "pip", "uninstall", "tensorflow", "tensorflow-cpu", "-y"])
        # Install compatible TensorFlow CPU version
        run([py, "-m", "pip", "install", "tensorflow-cpu==2.16.1"])
        # Install compatible OpenCV and numpy versions
        run([py, "-m", "pip", "install", "opencv-python==4.8.1.78", "numpy==1.26.4"])
    except subprocess.CalledProcessError:
        print("[!] TensorFlow CPU installation failed, trying fallback...")
        # Fallback: install latest CPU version
        run([py, "-m", "pip", "install", "tensorflow-cpu", "opencv-python==4.8.1.78", "numpy==1.26.4"])
    
    # Install other requirements
    req = ROOT / "requirements.txt"
    if req.exists():
        print("[+] Installing other requirements...")
        run([py, "-m", "pip", "install", "-r", str(req)])
    else:
        print("[!] requirements.txt not found; skipping.")

    # Validate torch; install CPU wheel if missing
    code = "import importlib,sys; sys.exit(0 if importlib.util.find_spec('torch') else 1)"
    rc = subprocess.call([py, "-c", code])
    if rc != 0:
        print("[+] Installing CPU-only PyTorch wheels")
        run([py, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"])


def launch_app():
    py = venv_python()
    run([py, str(ROOT / "RUN_FIRST.py")])


def main():
    ensure_venv()
    install_requirements()
    launch_app()


if __name__ == "__main__":
    main()


