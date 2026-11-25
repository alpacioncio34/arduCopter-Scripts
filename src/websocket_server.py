"""Servidor WebSocket: cada boton del ESP32 lanza una funcion de Python.

pip install websockets
python server.py
"""
import asyncio
import csv
import time
import websockets
from drone_actions import *

HOST, PORT = "0.0.0.0", 8765

master = connect_to_drone()

wait_for_heartbeat(master)

# Drone's actions will be the same as in manual control (see: manual_control.py)
def forward_press():
    # TODO: Start moving forward
    #print("forward pressed")
    set_speed_local(master,5,0,0,0)

def forward_release():
    # TODO: Stop moving forward
    #print("forward released")
    set_speed_local(master,0,0,0,0)

def backward_press():
    # TODO: Start moving backward
    #print("backward pressed")
    set_speed_local(master,-5,0,0,0)

def backward_release():
    # TODO: Stop moving backward
    #print("backward released")
    set_speed_local(master,0,0,0,0)

def left_press():
    # TODO: Start moving left
    #print("left pressed")
    set_speed_local(master,0,-5,0,0)

def left_release():
    # TODO: Stop moving left
    #print("left released")
    set_speed_local(master,0,0,0,0)

def right_press():
    # TODO: Start moving right
    #print("right pressed")
    set_speed_local(master,0,5,0,0)

def right_release():
    # TODO: Stop moving right
    #print("right released")
    set_speed_local(master,0,0,0,0)

def yaw_left_press():
    # TODO: Start rotating counterclockwise
    #print("yaw_left pressed")
    set_speed_local(master,0,0,0,-5)

def yaw_left_release():
    # TODO: Stop rotating
    #print("yaw_left released")
    set_speed_local(master,0,0,0,0)

def yaw_right_press():
    # TODO: Start rotating clockwise
    print("yaw_right pressed")
    set_speed_local(master,0,0,0,5)

def yaw_right_release():
    # TODO: Stop rotating
    print("yaw_right released")
    set_speed_local(master,0,0,0,0)

def up_press():
    # TODO: Start ascending
    #print("up pressed")
    set_speed_local(master,0,0,-5,0)

def up_release():
    # TODO: Stop ascending
    #print("up released")
    set_speed_local(master,0,0,0,0)

def down_press():
    # TODO: Start descending
    #print("down pressed")
    set_speed_local(master,0,0,5,0)

def down_release():
    # TODO: Stop descending
    #print("down released")
    set_speed_local(master,0,0,0,0)


ACTIONS = {
    1: (up_press, up_release),
    2: (down_press, down_release),
    3: (left_press, left_release),
    4: (forward_press, forward_release),
    5: (backward_press, backward_release),
    6: (right_press, right_release),
    7: (yaw_left_press, yaw_left_release),
    8: (yaw_right_press, yaw_right_release),
}

log_file = open("latencias.csv", "a", newline="")
log = csv.writer(log_file)


async def handler(ws):
    print("ESP32 conectado:", ws.remote_address)
    loop = asyncio.get_running_loop()
    async for msg in ws:
        t_rx = time.perf_counter()
        # Formatos:  "B,<id>,<seq>,<1=pulsa|0=suelta>"
        #            "L,<seq>,<rtt_us>" latencia medida por el ESP32
        parts = msg.split(",")
        if parts[0] == "B":
            btn, seq, pressed = int(parts[1]), int(parts[2]), int(parts[3])
            await ws.send(f"A,{seq}")  # ack inmediato (el ESP32 mide el RTT)
            on_press, on_release = ACTIONS.get(btn, (None, None))
            fn = on_press if pressed else on_release
            if fn:
                await loop.run_in_executor(None, fn)
        elif parts[0] == "L":
            seq, rtt_us = int(parts[1]), int(parts[2])
            log.writerow([time.time(), seq, rtt_us])
            log_file.flush()
            print(f"seq {seq}: RTT {rtt_us / 1000:.1f} ms")


async def main():
    async with websockets.serve(handler, HOST, PORT, ping_interval=None):
        print(f"Escuchando en ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
