"""
Detecta una mano con la cámara (MediaPipe) y escribe un mensaje por consola
cuando hay un único dedo (el índice) apuntando hacia arriba.

Instalación:
    pip install opencv-python mediapipe

Salir: pulsa 'q' en la ventana de vídeo.
"""

import math
from pathlib import Path
from drone_actions import stop_command
import subprocess
import sys
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils

# Modelo de MediaPipe Tasks (la antigua API mp.solutions ya no existe).
# Descarga: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
MODEL_PATH = Path(__file__).with_name("hand_landmarker.task")
TAKEOFF_SCRIPT = Path(__file__).with_name("drone_takeoff_test.py")
HAND_CONNECTIONS =vision.HandLandmarksConnections.HAND_CONNECTIONS

# Índices de landmarks de MediaPipe
WRIST = 0
THUMB_IP, THUMB_TIP = 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_PIP, MIDDLE_TIP = 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def solo_indice_arriba(lm):
    """True si solo el índice está extendido y apuntando hacia arriba."""
    # En imagen, "arriba" = y menor.
    indice_extendido = lm[INDEX_TIP].y < lm[INDEX_PIP].y < lm[INDEX_MCP].y

    # Los otros tres dedos deben estar doblados (punta más abajo que su PIP)
    medio_doblado = lm[MIDDLE_TIP].y > lm[MIDDLE_PIP].y
    anular_doblado = lm[RING_TIP].y > lm[RING_PIP].y
    menique_doblado = lm[PINKY_TIP].y > lm[PINKY_PIP].y

    # Pulgar doblado: su punta no está más lejos del meñique que su articulación
    # (así funciona sin importar si es mano izquierda o derecha)
    pulgar_doblado = dist(lm[THUMB_TIP], lm[PINKY_MCP]) <= dist(lm[THUMB_IP], lm[PINKY_MCP])

    return (
        indice_extendido
        and medio_doblado
        and anular_doblado
        and menique_doblado
        and pulgar_doblado
    )


def main():
    if not MODEL_PATH.exists():
        print(f"Falta el modelo: {MODEL_PATH}")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    ya_detectado = False  # para no imprimir en cada frame
    takeoff_proc = None

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )

    with vision.HandLandmarker.create_from_options(options) as hands:
        t_ms = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)  # efecto espejo
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            t_ms += 33  # timestamp estrictamente creciente
            resultado = hands.detect_for_video(imagen, t_ms)

            detectado = False
            for landmarks in resultado.hand_landmarks:
                drawing_utils.draw_landmarks(frame, landmarks, HAND_CONNECTIONS)
                if solo_indice_arriba(landmarks):
                    detectado = True

            if not detectado and ya_detectado:
                if takeoff_proc is not None:
                    stop_command()
                    takeoff_proc.kill()
            
            if detectado and not ya_detectado:
                print("☝️  Un solo dedo apuntando hacia arriba")
                #if takeoff_proc is None:  # solo se despega una vez
                print("Lanzando despegue...")
                takeoff_proc = subprocess.Popen([sys.executable, str(TAKEOFF_SCRIPT)])
            ya_detectado = detectado

            if detectado:
                cv2.putText(frame, "Taking off", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

            cv2.imshow("Hand tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
