'''
    The idea of the test is that the drone takes off and then follows the gps coordinates on a given file, for now, the coordinates are just written
    in a gps_data.txt file, in order for this to work on real life, data parsing would be needed, or perhaps a change of format.
'''

from drone_actions import connect_to_drone, arm_motors, takeoff, follow_gps
import subprocess
import time

HEIGHT = 40

# Taking off
if __name__ == "__main__":
    master = connect_to_drone()

    arm_motors(master)

    takeoff(HEIGHT)

    # Launching the walking simulator subprocess
    subprocess.Popen("walk_sim.py")

    time.sleep(5)

    follow_gps(master)
