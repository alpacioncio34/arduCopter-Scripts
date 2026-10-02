from pymavlink import mavutil
from drone_actions import connect_to_drone

master = connect_to_drone()
print("Listening for DISTANCE_SENSOR...")

while True:
    msg = master.recv_match(type='GLOBAL_POSITION_INT',blocking=True, timeout=5)
    if msg is None:
        print("No message was recieved")
        continue
    print(msg)