"""Prepare the environment and start the Windows demo."""
from pathlib import Path
import importlib.util
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    if sys.platform != "win32":
        print("Run this demo launcher on Windows.")
        return 1
    try:
        if any(importlib.util.find_spec(name) is None
               for name in ("cv2", "mediapipe", "pyautogui")):
            run("-m", "pip", "install", "-r", "requirements.txt")
        run("download_model.py")
        run("webcam.py")
        return 0
    except subprocess.CalledProcessError as error:
        print(f"Step failed with exit code {error.returncode}. See the output above.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
