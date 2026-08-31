from pymavlink import mavutil
import time

# In order to obtain a better security, we will wait for ACK in some given messages, this will confirm that the drone has received the message and is executing it. In this case, we will wait for ACK in the following messages:
def wait_for_ack(master, command,timeout=3):
    while True:
        # We listen only for ACK messages, and we will check if the command is the one we are waiting for
        ack_msg = master.recv_match(type='COMMAND_ACK', blocking=True, timeout=timeout)

        if ack_msg is None:
            print(f"No ACK received for command {command} within {timeout} seconds.")
            return False

        if ack_msg.command == command:
            if ack_msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"ACK received for command {command}: ACCEPTED")
                return True
            else:
                print(f"ACK received for command {command}: REJECTED with result {ack_msg.result}")
                return False

# Printing all the telemetry messages received from the drone given X seconds
def print_telemetry_seconds(master, duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        msg = master.recv_match(blocking=True)
        if msg is not None:
            print(msg)

# Printing all the telemetry messages received from the drone
def print_telemetry(master):
    while True:
        #bloquing=True means that the function will wait until a message is received before continuing
        msg = master.recv_match(blocking=True)
        if msg is not None:
            print(msg)

# Connect to the SITL
def connect_to_drone():
    conexion_string = 'udp:127.0.0.1:14550'
    master = mavutil.mavlink_connection(conexion_string)
    return master

# Confirm drone connection and wait for heartbeat
def wait_for_heartbeat(master):
    print("Waiting for dron heartbeat..")
    master.wait_heartbeat()
    print("¡Connection established!")

def change_mode(master, mode_name):
    mode_id = master.mode_mapping()[mode_name]
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id,
        0, 0, 0, 0, 0
    )
    print("Mode changed to", mode_name)
    return wait_for_ack(master, mavutil.mavlink.MAV_CMD_DO_SET_MODE)
# Arm the motors
def arm_motors(master):
    print("Armando motores...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, # Confirmation
        1, # 1 arm, 0 disarm
        0, 0, 0, 0, 0, 0 
    )
    # Wait for confirmation
    master.motors_armed_wait()
    print("¡Motors armed!")


def takeoff(master, height):
    print(f"Taking off to {height} meters...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, 
        height
    )
    if not wait_for_ack(master, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF):
        print("Takeoff rejected.")
        return False
    # Wait for the drone to reach the desired altitude
    reached = False
    while not reached:
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg is not None:
            current_altitude = msg.relative_alt / 1000.0  # Convert to meters
            print(f"Current altitude: {current_altitude:.2f} m")
            if current_altitude >= height:
                reached = True
                print("Target altitude reached!")


# z = 0 is the ground level, so if we want to go up, we need to set a negative value for z. For example, if we want to go up 10 meters, we need to set z = -10. If we want to go down 10 meters, we need to set z = 10.
def go_to_local(master, x, y, z):
    master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
        10,  # time_boot_ms (not used)
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # Coordinate frame
        0b0000111111111000,  # Type mask: ignore velocity and acceleration
        x,  # X position (North)
        y,  # Y position (East)
        z,  # Z position (Down)
        0,  # X velocity (not used)
        0,  # Y velocity (not used)
        0,  # Z velocity (not used)
        0,  # X acceleration (not used)
        0,  # Y acceleration (not used)
        0,  # Z acceleration (not used)
        0,  # Yaw (not used) 
        0   # Yaw rate (not used)
    ))

def go_to(master, lat, lon, altitude=10):
    # Scaling the latitude and longitude to the required format (degrees * 1e7)
    lat = int(lat * 1e7)
    lon = int(lon * 1e7)
    master.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(
        10,  # time_boot_ms (not used)
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Coordinate frame
        0b0000111111111000,  # Type mask: ignore velocity and   acceleration
        lat,  # Latitude (scaled)
        lon,  # Longitude (scaled)
        altitude,  # Altitude (meters)  
        0,  # X velocity (not used)
        0,  # Y velocity (not used)
        0,  # Z velocity (not used)
        0,  # X acceleration (not used)
        0,  # Y acceleration (not used)
        0,  # Z acceleration (not used)
        0,  # Yaw (not used)
        0   # Yaw rate (not used)
    ))

def set_speed(master,speed):
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
        0,  # Confirmation
        1,  # Speed type (1 = airspeed, 2 = groundspeed)
        speed,  # Speed value
        -1,  # Throttle (not used)
        0, 0, 0, 0
    )

def land(master):
    change_mode(master, "LAND")
    # Wait for the drone to land
    reached = False
    while not reached:
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg is not None:
            current_altitude = msg.relative_alt / 1000.0  # Convert to meters
            print(f"Current altitude: {current_altitude:.2f} m")
            if current_altitude == 0:
                reached = True
                print("Target altitude reached!")

def follow_gps(master):
    '''
    This function consists of 2 parts, the first one reads the data from the source 
    (in this case, the walk_sim.py script) and the second one sends the data to the drone, using go_to.
    '''
    while True:
        # Read GPS data from the source
        with open("gps_data.txt", "r") as file:
            gps_data = file.read().strip()
            if gps_data:
                lat, lon = map(float, gps_data.split(","))
                print(f"Received GPS data -> Latitude: {lat:.6f} | Longitude: {lon:.6f}")
                # Send the GPS data to the drone
                go_to(master, lat, lon)

def close_connection(master):
    print("Closing connection...")
    master.close()
