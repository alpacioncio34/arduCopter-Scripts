import tkinter as tk
from drone_actions import set_speed_local, connect_to_drone, wait_for_heartbeat

# Keyboard auto-repeat sends fake release/press pairs while a key is held down.
# A release is only considered real if no new press arrives within this time.
KEY_RELEASE_DEBOUNCE_MS = 50

master = connect_to_drone()

wait_for_heartbeat(master=master)

class ManualControl:
    def __init__(self, root):
        self.root = root
        self.root.title("Manual Control")

        # action: (button label, keyboard key, grid row, grid column, on press, on release)
        self.actions = {
            "forward":   ("▲\nForward (W)",   "w",    0, 1, self.forward_press,   self.forward_release),
            "backward":  ("▼\nBackward (S)",  "s",    2, 1, self.backward_press,  self.backward_release),
            "left":      ("◀\nLeft (A)",      "a",    1, 0, self.left_press,      self.left_release),
            "right":     ("▶\nRight (D)",     "d",    1, 2, self.right_press,     self.right_release),
            "yaw_left":  ("↺\nYaw left (Q)",  "q",    0, 0, self.yaw_left_press,  self.yaw_left_release),
            "yaw_right": ("↻\nYaw right (E)", "e",    0, 2, self.yaw_right_press, self.yaw_right_release),
            "up":        ("⤒\nUp (↑)",        "up",   0, 4, self.up_press,        self.up_release),
            "down":      ("⤓\nDown (↓)",      "down", 2, 4, self.down_press,      self.down_release),
        }
        self.key_to_action = {entry[1]: action for action, entry in self.actions.items()}

        self.active = set()          # Actions currently being held
        self.pending_releases = {}   # action -> id of the scheduled (debounced) key release
        self.buttons = {}

        self.build_ui()

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        # If the window loses focus we would never see the release, so stop everything
        self.root.bind("<FocusOut>", self.release_all)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack()

        for action, (label, _key, row, column, _press, _release) in self.actions.items():
            button = tk.Button(frame, text=label, width=12, height=3)
            button.grid(row=row, column=column, padx=4, pady=4)
            button.bind("<ButtonPress-1>", lambda event, a=action: self.on_press(a))
            button.bind("<ButtonRelease-1>", lambda event, a=action: self.on_release(a))
            self.buttons[action] = button

        # Empty column separating the horizontal controls from the altitude ones
        frame.grid_columnconfigure(3, minsize=30)

        self.status = tk.Label(self.root, text="Idle", pady=8)
        self.status.pack()

    # ------------------------------------------------------------------
    # Press / release plumbing (shared by mouse and keyboard)
    # ------------------------------------------------------------------
    def on_press(self, action):
        if action in self.active:
            return
        self.active.add(action)
        self.buttons[action].config(relief=tk.SUNKEN)
        self.update_status()
        self.actions[action][4]()

    def on_release(self, action):
        if action not in self.active:
            return
        self.active.discard(action)
        self.buttons[action].config(relief=tk.RAISED)
        self.update_status()
        self.actions[action][5]()

    def on_key_press(self, event):
        action = self.key_to_action.get(event.keysym.lower())
        if action is None:
            return
        # A press right after a release means auto-repeat: the key is still held
        pending = self.pending_releases.pop(action, None)
        if pending is not None:
            self.root.after_cancel(pending)
        self.on_press(action)

    def on_key_release(self, event):
        action = self.key_to_action.get(event.keysym.lower())
        if action is None or action in self.pending_releases:
            return
        self.pending_releases[action] = self.root.after(
            KEY_RELEASE_DEBOUNCE_MS, lambda: self.finish_key_release(action)
        )

    def finish_key_release(self, action):
        self.pending_releases.pop(action, None)
        self.on_release(action)

    def release_all(self, event=None):
        for pending in self.pending_releases.values():
            self.root.after_cancel(pending)
        self.pending_releases.clear()
        for action in list(self.active):
            self.on_release(action)

    def update_status(self):
        self.status.config(text=", ".join(sorted(self.active)) if self.active else "Idle")

    def on_close(self):
        self.release_all()
        # TODO: Close the drone connection (drone_actions.close_connection)
        self.root.destroy()

    # ------------------------------------------------------------------
    # Functionality: called once when the control is pressed and once when it is released
    # ------------------------------------------------------------------
    def forward_press(self):
        # TODO: Start moving forward
        #print("forward pressed")
	    set_speed_local(master,5,0,0,0)

    def forward_release(self):
        # TODO: Stop moving forward
        #print("forward released")
	    set_speed_local(master,0,0,0,0)

    def backward_press(self):
        # TODO: Start moving backward
        #print("backward pressed")
        set_speed_local(master,-5,0,0,0)

    def backward_release(self):
        # TODO: Stop moving backward
        #print("backward released")
        set_speed_local(master,0,0,0,0)

    def left_press(self):
        # TODO: Start moving left
        #print("left pressed")
        set_speed_local(master,0,-5,0,0)

    def left_release(self):
        # TODO: Stop moving left
        #print("left released")
        set_speed_local(master,0,0,0,0)

    def right_press(self):
        # TODO: Start moving right
        #print("right pressed")
        set_speed_local(master,0,5,0,0)

    def right_release(self):
        # TODO: Stop moving right
        #print("right released")
        set_speed_local(master,0,0,0,0)

    def yaw_left_press(self):
        # TODO: Start rotating counterclockwise
        #print("yaw_left pressed")
        set_speed_local(master,0,0,0,-5)

    def yaw_left_release(self):
        # TODO: Stop rotating
        #print("yaw_left released")
        set_speed_local(master,0,0,0,0)

    def yaw_right_press(self):
        # TODO: Start rotating clockwise
        #print("yaw_right pressed")
        set_speed_local(master,0,0,0,5)

    def yaw_right_release(self):
        # TODO: Stop rotating
        #print("yaw_right released")
        set_speed_local(master,0,0,0,0)
        
    def up_press(self):
        # TODO: Start ascending
        print("up pressed")

    def up_release(self):
        # TODO: Stop ascending
        print("up released")

    def down_press(self):
        # TODO: Start descending
        print("down pressed")

    def down_release(self):
        # TODO: Stop descending
        print("down released")


if __name__ == "__main__":
    root = tk.Tk()
    # TODO: Connect to the drone here (drone_actions.connect_to_drone / wait_for_heartbeat)
    app = ManualControl(root)
    root.mainloop()
