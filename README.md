# Gesture Control

Control your mouse with a webcam and hand gestures. Built with Python, OpenCV, MediaPipe and PyAutoGUI as a learning and portfolio project.

The application tracks one hand, draws its landmarks in real time and translates gestures into mouse actions. Frames are processed locally; this application does not record or upload video.

## Controls

Each pinch pairs your thumb with another finger.

| Gesture | Action |
| --- | --- |
| Move your index finger with fingers open | Move the cursor |
| Brief thumb–index pinch, then release | Left click |
| Hold thumb–index pinch for 0.20 seconds | Drag |
| Open thumb–index pinch while dragging | Release the mouse button |
| Thumb–middle pinch, then release | Double click |
| Thumb–ring pinch and vertical hand movement | Scroll |

Separate your fingers between gestures. The closest finger to the thumb selects the gesture; it stays selected until release.

Scroll is inverted: move your hand up to scroll down, or down to scroll up. Moving farther from the starting wrist position increases speed. Return to that position to stop scrolling, or open the pinch to end the gesture.

## Start with a double click

Install Python 3.11, extract the project and double-click **RUN_DEMO.bat**.

On the first run, the launcher creates a local `.venv`, installs missing dependencies and downloads the hand model. This needs Internet access and may take a few minutes. Later runs reuse those files. Keep using the same extracted folder.

Select the webcam preview and press **C** to enable control. **Q** exits while the preview has focus. Python is required; there is no compiled executable in this project.

## Setup on Windows

Development environment: Windows, Python 3.11.9 and an integrated webcam. Install Python 3.11 and open a PowerShell terminal in the project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_model.py
.\.venv\Scripts\python.exe webcam.py
```

These commands use the virtual environment directly, without activating it. An Internet connection is needed for dependencies and the model; tracking then runs locally. You can reuse your existing working environment and model. The model belongs beside `webcam.py` and is not included in the repository.

## Using the app

Select the webcam preview and press **C** to enable control. Show your whole hand and open your fingers before making a gesture.

- **C** toggles control; **Q** exits. Both require the preview window to have focus.
- **Ctrl+C** stops the program from the focused terminal.
- Moving the physical mouse to a primary-screen corner triggers PyAutoGUI's failsafe on the next mouse operation.

Clicking another application can move focus away from the preview. To scroll, place the cursor over scrollable content and select the target window if needed. The mouse button is released when the app exits, pauses or loses the hand beyond its timeout.

## Tracking area

The rectangle covers the original 15%–85% region of the webcam image. It maps cursor movement to the screen; it does **not** restrict gesture recognition. The full frame is processed, including outside the rectangle. Cursor coordinates are clamped with a five-pixel screen margin.

Pinches use the original 2D finger distances divided by palm width. There is no depth correction. Occlusion, poor lighting and hand orientation can affect recognition, even when landmarks are visible.

## Configuration

Settings are at the top of `webcam.py`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `CAMERA_INDEX` | `0` | Webcam selection |
| `CURSOR_SMOOTHING` | `0.35` | Cursor response |
| `DRAG_SMOOTHING` | `0.45` | Drag response |
| `PINCH_CLOSE` | `0.40` | Start a pinch |
| `PINCH_READY` | `0.60` | Prepare the next gesture |
| `DRAG_RELEASE` | `0.80` | Opening needed to release a drag |
| `DRAG_START_TIME` | `0.20` | Hold time before dragging |
| `DRAG_RELEASE_TIME` | `0.08` | Drag release confirmation |
| `SCROLL_DEAD_ZONE` | `3` | Minimum wrist offset in pixels |
| `PIXELS_PER_SCROLL_LEVEL` | `5` | Offset per speed increase |
| `MAX_SCROLL_SPEED` | `12` | Maximum steps per command |

## Files

| File | Purpose |
| --- | --- |
| `webcam.py` | Tracking, gesture states and mouse control |
| `download_model.py` | Official model download |
| `requirements.txt` | Direct dependencies |
| `.gitignore` | Excludes the environment, model and temporary files |
| `.gitattributes` | Text line endings |
| `RUN_DEMO.bat` | Double-click launcher for Windows |
| `windows_tools.py` | Dependency setup and application startup |
| `REFERENCES.md` | Upstream documentation and model source |

## Troubleshooting

- **Camera unavailable:** close other camera apps, check Windows camera permissions, or try `CAMERA_INDEX = 1`.
- **Missing model:** run `download_model.py`.
- **Gesture not selected:** open your fingers first and avoid bringing several fingers to the thumb together.
- **Scroll detected but nothing moves:** check that the target content can scroll and that the cursor is over it.
- **Stopped at a corner:** move the physical mouse away from the corner before restarting.
- **Elevated applications do not respond:** test in a regular window; Windows may restrict input across privilege levels.

## Validation and dependencies

The Portuguese version was tested interactively during development. Syntax checks and simulated click, double-click, drag, scroll and cleanup sequences were run during packaging. The English version has also been syntax-checked; it still needs a webcam test after renaming. Multi-monitor behavior has not been validated; this version targets the primary screen.

Dependencies are not pinned to the author's exact environment. To capture your own working setup:

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 requirements-lock.txt
```

You can then install with `-r requirements-lock.txt`. Generate it from a dedicated, working project environment.

## What this project explores

Real-time video processing, hand tracking, coordinate mapping, gesture state machines, input smoothing and resource cleanup. The pretrained hand model comes from Google; it was not trained as part of this project.
