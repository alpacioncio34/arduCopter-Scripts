from drone_actions import connect_to_drone, follow_gps, go_to, go_to_local, set_speed, wait_for_heartbeat, change_mode, arm_motors, takeoff,  land
from time import sleep

if __name__ == "__main__":
    # Connect to the drone
    master = connect_to_drone()

    # Wait for the drone's heartbeat
    wait_for_heartbeat(master)

    # Start a separate thread to print telemetry messages
    #telemetry_thread = threading.Thread(target=print_telemetry, args=(master,))
    #telemetry_thread.daemon = True  # This makes the thread exit when the main program exits
    #telemetry_thread.start()

    # Change flight mode to GUIDED
    change_mode(master, "GUIDED")

    # Arm the motors
    arm_motors(master)

    # Take off to a height of 10 meters
    takeoff(master, 50)

    sleep(5)  # Wait for a few seconds to ensure the drone has taken off

    #go_to_local(master, 10, 20, -10)  # Example coordinates and altitude
    go_to(master, 35.8867,5.3000) 

    #set_speed(master, 10)  # Set speed to 10 m/s
    #follow_gps(master)  # Follow the path defined in gps_data.txt with a speed of 5 m/s
