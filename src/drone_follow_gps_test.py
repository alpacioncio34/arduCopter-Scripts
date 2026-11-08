'''
    The idea of the test is that the drone takes off and then follows the gps coordinates on a given file, for now, the coordinates are just written
    in a gps_data.txt file, in order for this to work on real life, data parsing would be needed, or perhaps a change of format.
'''

from drone_actions import connect_to_drone, arm_motors, takeoff, follow_gps, wait_for_heartbeat, change_mode
import subprocess
import time
import sys
from pathlib import Path
WALK_SCRIPT = Path(__file__).with_name("walk_sim.py")


HEIGHT = 40

# Taking off
if __name__ == "__main__":
    master = connect_to_drone()

    wait_for_heartbeat(master=master)

    change_mode(master,"GUIDED")

    arm_motors(master)

    takeoff(master,HEIGHT)

    # Launching the walking simulator subprocess
    takeoff_proc = subprocess.Popen([sys.executable, str(WALK_SCRIPT)])

    time.sleep(5)

    follow_gps(master)
