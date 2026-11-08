"""
Hand-gesture drone control using the webcam (MediaPipe Hand Landmarker).

Behaviour
---------
* When exactly ONE finger (the index) is extended and pointing up, and the
  gesture has been held for a few consecutive frames, the drone takes off.
* When the gesture disappears (held for a few consecutive frames), the drone
  is switched to LOITER mode (stop_command).

Drone commands are slow and blocking (MAVLink connection, heartbeat, sleeps,
ACK waits). To keep the video window responsive they run on a single
background worker thread. Using ONE worker also guarantees that "takeoff" and
"stop" never run at the same time and always execute in the order requested.

Install:
    pip install opencv-python mediapipe

Quit: press 'q' in the video window.
"""

import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.vision import drawing_utils

from drone_actions import stop_command, takeoff_wrapper

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# MediaPipe Tasks model (the old mp.solutions API no longer exists).
# Download: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
MODEL_PATH = Path(__file__).with_name("hand_landmarker.task")
HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS

TAKEOFF_HEIGHT_M = 40  # Target altitude passed to takeoff_wrapper

# Debounce: how many consecutive frames must agree before we act.
# This avoids triggering the drone because of a single misdetected frame
# and avoids rapid takeoff/stop toggling when detection flickers.
# At ~30 FPS, 10 frames is roughly 0.3 s.
FRAMES_TO_CONFIRM = 10

# --------------------------------------------------------------------------- #
# MediaPipe landmark indices
# https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
# --------------------------------------------------------------------------- #
THUMB_IP, THUMB_TIP = 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_PIP, MIDDLE_TIP = 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20
FILE_PATH = Path(__file__).with_name("debud_test.py")


def dist(a, b):
    """2D distance between two normalized landmarks."""
    return math.hypot(a.x - b.x, a.y - b.y)


def only_index_up(lm):
    """Return True if only the index finger is extended and pointing up."""
    # In image coordinates y grows downwards, so "up" means a smaller y.
    # The index is extended when tip, PIP and MCP are stacked going upwards.
    index_extended = lm[INDEX_TIP].y < lm[INDEX_PIP].y < lm[INDEX_MCP].y

    # The other three fingers must be folded: tip below its PIP joint.
    middle_folded = lm[MIDDLE_TIP].y > lm[MIDDLE_PIP].y
    ring_folded = lm[RING_TIP].y > lm[RING_PIP].y
    pinky_folded = lm[PINKY_TIP].y > lm[PINKY_PIP].y

    # Thumb folded: its tip is not farther from the pinky base than its IP
    # joint. Using distance (instead of x position) makes this work for both
    # left and right hands.
    thumb_folded = dist(lm[THUMB_TIP], lm[PINKY_MCP]) <= dist(lm[THUMB_IP], lm[PINKY_MCP])

    return (
        index_extended
        and middle_folded
        and ring_folded
        and pinky_folded
        and thumb_folded
    )


def run_takeoff():
    takeoff_wrapper(height=TAKEOFF_HEIGHT_M)


def run_stop():
    """Runs on the worker thread. stop_command is a regular blocking function."""
    try:
        stop_command()
    except Exception as e:
        print(f"Stop command failed: {e}")


def main():
    if not MODEL_PATH.exists():
        print(f"Missing model file: {MODEL_PATH}")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open the camera.")
        return

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )

    # Single worker: drone commands run one at a time, in order.
    # executor = ThreadPoolExecutor(max_workers=1)

    gesture_active = False  # Confirmed (debounced) state of the gesture
    streak = 0              # Consecutive frames that disagree with gesture_active
    start = time.monotonic()
    last_ts_ms = -1

    try:
        with vision.HandLandmarker.create_from_options(options) as hands:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame = cv2.flip(frame, 1)  # mirror effect
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                # VIDEO mode requires strictly increasing timestamps (ms).
                ts_ms = max(int((time.monotonic() - start) * 1000), last_ts_ms + 1)
                last_ts_ms = ts_ms
                result = hands.detect_for_video(image, ts_ms)

                # Raw detection for THIS frame.
                detected = False
                for landmarks in result.hand_landmarks:
                    drawing_utils.draw_landmarks(frame, landmarks, HAND_CONNECTIONS)
                    if only_index_up(landmarks):
                        detected = True

                # Debounce: only change the confirmed state after
                # FRAMES_TO_CONFIRM consecutive frames that disagree with it.
                if detected != gesture_active:
                    streak += 1
                    if streak >= FRAMES_TO_CONFIRM:
                        gesture_active = detected
                        streak = 0
                        if gesture_active:
                            print("Gesture confirmed -> taking off")
                            # executor.submit(run_takeoff)
                            subprocess.Popen([sys.executable,str(FILE_PATH)])
                        else:
                            print("Gesture lost -> stopping (LOITER)")
                            run_stop()
                else:
                    streak = 0

                if gesture_active:
                    cv2.putText(frame, "Taking off", (20, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                cv2.imshow("Hand tracking", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        # Always release the camera, even if something above raised.
        cap.release()
        cv2.destroyAllWindows()
        # Let any in-flight drone command finish before exiting.
        # executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
