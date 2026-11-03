"""Download the official Hand Landmarker model."""
from pathlib import Path
from urllib.request import urlopen
import shutil

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = Path(__file__).resolve().parent / "hand_landmarker.task"


def main():
    if MODEL_PATH.is_file() and MODEL_PATH.stat().st_size:
        print("Model already downloaded.")
        return 0
    temporary = MODEL_PATH.with_suffix(".task.part")
    try:
        print("Downloading Hand Landmarker...")
        # Only replace the target once the download is complete.
        with urlopen(MODEL_URL, timeout=60) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        if not temporary.stat().st_size:
            raise RuntimeError("Downloaded an empty file.")
        temporary.replace(MODEL_PATH)
        print("Model ready.")
        return 0
    except Exception as error:
        print(f"Download failed: {error}")
        return 1
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
