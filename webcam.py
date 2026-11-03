# Webcam mouse control. C toggles control; Q exits the preview.
from pathlib import Path
import math
import time

import cv2
import mediapipe as mp
import pyautogui

MODEL_PATH = Path(__file__).resolve().parent / "hand_landmarker.task"
CAMERA_INDEX = 0
WINDOW_NAME = "Gesture Control"

AREA_START = 0.15
AREA_END = 0.85
AREA_SIZE = AREA_END - AREA_START

CURSOR_SMOOTHING = 0.35
DRAG_SMOOTHING = 0.45

# Pinch distances are relative to palm width.
PINCH_CLOSE = 0.40
PINCH_READY = 0.60
PINCH_RELEASE = 0.75
DRAG_RELEASE = 0.80

MIN_CLICK_TIME = 0.06
DRAG_START_TIME = 0.20
RELEASE_TIME = 0.12
DRAG_RELEASE_TIME = 0.08
HAND_LOSS_TIMEOUT = 0.25
DRAG_LOSS_TIMEOUT = 0.50
DOUBLE_CLICK_INTERVAL = 0.12

# moving your hand up scrolls the page down
SCROLL_INTERVAL = 0.03
SCROLL_DEAD_ZONE = 3
PIXELS_PER_SCROLL_LEVEL = 5
MAX_SCROLL_SPEED = 12

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
]

def distance(hand, a, b, width, height):
    
    return math.hypot(
        (hand[a].x - hand[b].x) * width,
        (hand[a].y - hand[b].y) * height,
    )

def clamp_position(x, y, screen_width, screen_height):
    
    return (
        max(5, min(screen_width - 6, x)),
        max(5, min(screen_height - 6, y)),
    )

def release_button():
    
    # Release must still work after a failsafe exception.
    failsafe = pyautogui.FAILSAFE
    try:
        pyautogui.FAILSAFE = False
        pyautogui.mouseUp(button="left")
    finally:
        pyautogui.FAILSAFE = failsafe

def draw_text(frame, text, y, color=(0, 255, 255), scale=0.5):
    
    cv2.putText(
        frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
        scale, color, 2,
    )

def main():
    
    if not MODEL_PATH.is_file():
        print("Model not found. Run: python download_model.py")
        return 1

    screen_width, screen_height = pyautogui.size()
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.01

    active = False
    mode = "ready"
    button_down = False
    cursor_x, cursor_y = pyautogui.position()

    pinch_started = None
    release_started = None
    hand_lost_at = None
    feedback = ""
    feedback_until = 0.0
    drag_wrist_x = drag_wrist_y = 0.0
    drag_start_x = drag_start_y = 0.0
    scroll_origin_y = None
    last_scroll_at = 0.0
    scroll_offset = 0.0
    scroll_steps = 0

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = None
    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(options) as detector:
            camera = cv2.VideoCapture(CAMERA_INDEX)
            if not camera.isOpened():
                raise RuntimeError("Could not open the webcam.")

            video_started = time.monotonic()
            last_timestamp_ms = -1

            while True:
                success, frame = camera.read()
                if not success:
                    raise RuntimeError("Could not read a webcam frame.")

                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]

                # Keep the full frame: the rectangle only maps cursor movement.
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                timestamp_ms = max(
                    int((time.monotonic() - video_started) * 1000),
                    last_timestamp_ms + 1,
                )
                last_timestamp_ms = timestamp_ms
                result = detector.detect_for_video(mp_frame, timestamp_ms)
                now = time.monotonic()
                hand_visible = bool(result.hand_landmarks)

                if hand_visible:
                    if hand_lost_at is not None:
                        release_started = None
                        scroll_origin_y = None
                        scroll_offset = 0.0
                        scroll_steps = 0
                    hand_lost_at = None
                elif hand_lost_at is None:
                    hand_lost_at = now

                loss_timeout = (
                    DRAG_LOSS_TIMEOUT if mode == "drag"
                    else HAND_LOSS_TIMEOUT
                )
                hand_timed_out = (
                    hand_lost_at is not None
                    and now - hand_lost_at >= loss_timeout
                )

                if not active or hand_timed_out:
                    if button_down:
                        release_button()
                        button_down = False
                    mode = "ready"
                    pinch_started = release_started = None
                    scroll_origin_y = None
                    scroll_offset = 0.0
                    scroll_steps = 0
                    cursor_x, cursor_y = pyautogui.position()

                if hand_visible:
                    hand = result.hand_landmarks[0]
                    points = [(int(p.x * width), int(p.y * height)) for p in hand]

                    for start, end in CONNECTIONS:
                        cv2.line(frame, points[start], points[end], (0, 255, 0), 2)
                    for x, y in points:
                        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                    for index, color in [(8, (0, 255, 255)), (12, (255, 0, 255)),
                                        (16, (255, 255, 0))]:
                        cv2.circle(frame, points[index], 10, color, 2)

                    # Keep the original 2D pinch measurement.
                    palm_width = max(distance(hand, 5, 17, width, height), 1.0)
                    pinches = {
                        "index": distance(hand, 4, 8, width, height) / palm_width,
                        "middle": distance(hand, 4, 12, width, height) / palm_width,
                        "ring": distance(hand, 4, 16, width, height) / palm_width,
                    }
                    wrist_x, wrist_y = hand[0].x, hand[0].y
                    fingers_open = all(v > PINCH_READY for v in pinches.values())

                    if active:
                        if mode == "ready":
                            if fingers_open:
                                mode = "move"

                        elif mode == "move":
                            closest_finger = min(pinches, key=pinches.get)
                            if pinches[closest_finger] < PINCH_CLOSE:
                                pinch_started = now
                                release_started = None
                                if closest_finger == "index":
                                    mode = "pinch"
                                elif closest_finger == "middle":
                                    mode = "double"
                                else:
                                    mode = "scroll"
                                    scroll_origin_y = wrist_y * height
                                    scroll_offset = 0.0
                                    scroll_steps = 0
                                    last_scroll_at = now
                            elif fingers_open:
                                x = (hand[8].x - AREA_START) / AREA_SIZE
                                y = (hand[8].y - AREA_START) / AREA_SIZE
                                target_x, target_y = clamp_position(
                                    5 + x * (screen_width - 11),
                                    5 + y * (screen_height - 11),
                                    screen_width, screen_height,
                                )
                                cursor_x += (target_x - cursor_x) * CURSOR_SMOOTHING
                                cursor_y += (target_y - cursor_y) * CURSOR_SMOOTHING
                                pyautogui.moveTo(int(cursor_x), int(cursor_y))

                        elif mode in ("pinch", "double"):
                            finger = "index" if mode == "pinch" else "middle"
                            if pinches[finger] > PINCH_READY:
                                if release_started is None:
                                    release_started = now
                                if now - release_started >= RELEASE_TIME:
                                    duration = release_started - pinch_started
                                    if duration >= MIN_CLICK_TIME:
                                        if mode == "double":
                                            pyautogui.doubleClick(interval=DOUBLE_CLICK_INTERVAL)
                                            feedback = "DOUBLE CLICK!"
                                        else:
                                            pyautogui.click()
                                            feedback = "CLICK!"
                                        feedback_until = time.monotonic() + 0.5
                                    mode = "ready"
                                    pinch_started = release_started = None
                            else:
                                release_started = None
                                if (mode == "pinch"
                                        and now - pinch_started >= DRAG_START_TIME):
                                    drag_start_x, drag_start_y = pyautogui.position()
                                    cursor_x, cursor_y = float(drag_start_x), float(drag_start_y)
                                    drag_wrist_x, drag_wrist_y = wrist_x, wrist_y
                                    button_down = True
                                    pyautogui.mouseDown(button="left")
                                    mode = "drag"

                        elif mode in ("drag", "scroll"):
                            finger = "index" if mode == "drag" else "ring"
                            release_threshold = (
                                DRAG_RELEASE if mode == "drag" else PINCH_RELEASE
                            )
                            release_delay = (
                                DRAG_RELEASE_TIME if mode == "drag"
                                else RELEASE_TIME
                            )
                            if pinches[finger] > release_threshold:
                                if release_started is None:
                                    release_started = now
                            else:
                                release_started = None

                            released = (
                                release_started is not None
                                and now - release_started >= release_delay
                            )
                            if released:
                                if button_down:
                                    release_button()
                                    button_down = False
                                mode = "ready"
                                pinch_started = release_started = None
                                scroll_origin_y = None
                                scroll_offset = 0.0
                                scroll_steps = 0
                            elif mode == "drag" or release_started is None:
                                if mode == "drag":
                                    target_x, target_y = clamp_position(
                                        drag_start_x + (wrist_x - drag_wrist_x)
                                        * screen_width / AREA_SIZE,
                                        drag_start_y + (wrist_y - drag_wrist_y)
                                        * screen_height / AREA_SIZE,
                                        screen_width, screen_height,
                                    )
                                    cursor_x += (target_x - cursor_x) * DRAG_SMOOTHING
                                    cursor_y += (target_y - cursor_y) * DRAG_SMOOTHING
                                    pyautogui.moveTo(int(cursor_x), int(cursor_y))
                                else:
                                    current_y = wrist_y * height
                                    if scroll_origin_y is None:
                                        scroll_origin_y = current_y
                                    scroll_offset = scroll_origin_y - current_y
                                    scroll_steps = 0
                                    if abs(scroll_offset) > SCROLL_DEAD_ZONE:
                                        speed = min(
                                            MAX_SCROLL_SPEED,
                                            1 + int((abs(scroll_offset) - SCROLL_DEAD_ZONE)
                                                    / PIXELS_PER_SCROLL_LEVEL),
                                        )
                                        scroll_steps = (-speed if scroll_offset > 0
                                                         else speed)
                                    if now - last_scroll_at >= SCROLL_INTERVAL:
                                        if scroll_steps:
                                            pyautogui.scroll(scroll_steps)
                                        last_scroll_at = now
                            else:
                                scroll_steps = 0

                cv2.rectangle(
                    frame,
                    (int(width * AREA_START), int(height * AREA_START)),
                    (int(width * AREA_END), int(height * AREA_END)),
                    (255, 255, 0), 2,
                )
                if not active:
                    message = "Press C to enable control"
                elif not hand_visible:
                    message = "Hand not visible"
                else:
                    message = {
                        "ready": "Separate your fingers to get ready",
                        "move": "Index: click | Middle: double click | Ring: scroll",
                        "pinch": "Release: click | Hold: drag",
                        "double": "Release thumb and middle finger to double-click",
                        "drag": "DRAGGING - open the pinch to release",
                        "scroll": "SCROLL - move your hand up to scroll down",
                    }[mode]
                if now < feedback_until:
                    message = feedback
                status = "ACTIVE" if active else "PAUSED"
                draw_text(frame, f"{status} | C: toggle | Q: quit", 30,
                         color=(0, 255, 0), scale=0.6)
                if mode == "scroll" and hand_visible:
                    draw_text(frame,
                             f"Offset: {scroll_offset:.0f}px | Scroll: {scroll_steps}",
                             60, color=(255, 0, 255), scale=0.55)
                draw_text(frame, message, height - 20, scale=0.45)

                cv2.imshow(WINDOW_NAME, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("c"):
                    if button_down:
                        release_button()
                        button_down = False
                    active = not active
                    mode = "ready"
                    pinch_started = release_started = None
                    scroll_origin_y = None
                    scroll_offset = 0.0
                    scroll_steps = 0
                    feedback_until = 0.0
                    cursor_x, cursor_y = pyautogui.position()
                elif key == ord("q"):
                    break

    except pyautogui.FailSafeException:
        print("Stopped: mouse reached a failsafe corner.")
    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as error:
        print(f"Error: {error}")
        return 1
    finally:
        try:
            if button_down:
                release_button()
        finally:
            if camera is not None:
                camera.release()
            cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
