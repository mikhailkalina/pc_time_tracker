import pythoncom
import wmi
import threading
import time
import tkinter as tk
from tkinter import ttk
import json
import os

SAVE_FILE = "worktime_data.json"

class WorkTimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Work Time Tracker")
        self.root.geometry("300x160")
        self.root.resizable(False, False)

        self.total_time = 0
        self.create_ui()
        self.resume()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Timer tick handler
        threading.Thread(target=self.update_timer, daemon=True).start()

        # WMI Sleep/Resume handler
        threading.Thread(target=self.watch_sleep_resume, daemon=True).start()

    def create_ui(self):
        self.label = ttk.Label(self.root, text="Work Time:", font=("Segoe UI", 14))
        self.label.pack(pady=10)

        self.time_label = ttk.Label(self.root, text=self.format_time(self.total_time), font=("Segoe UI", 20, "bold"))
        self.time_label.pack(pady=5)

        self.button = ttk.Button(self.root, text="Pause", command=self.toggle)
        self.button.pack(pady=10)

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.resume()

    def pause(self):
        self.running = False
        self.total_time += time.time() - self.start_time
        self.save_data()
        self.button.config(text="Resume")

    def resume(self):
        self.running = True
        self.start_time = time.time()
        self.load_data()
        self.button.config(text="Pause")

    def on_close(self):
        if self.running:
            self.pause()
        self.root.destroy()

    def format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    def save_data(self):
        data = {"total_time": int(self.total_time)}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                self.total_time = int(data.get("total_time", 0))
        else:
            self.total_time = 0

    # ---------------- Time tick ----------------
    def update_timer(self):
        while True:
            if self.running:
                elapsed = self.total_time + time.time() - self.start_time
                self.time_label.config(text=self.format_time(elapsed))
            else:
                self.time_label.config(text=self.format_time(self.total_time))
            time.sleep(1)

    # ---------------- WMI Sleep/Resume ----------------
    def watch_sleep_resume(self):
        c = wmi.WMI()
        watcher = c.Win32_PowerManagementEvent.watch_for()

        while True:
            pythoncom.PumpWaitingMessages()
            event = watcher()

            # Event codes:
            # 4 = entering sleep
            # 7 = resume from sleep
            if event.EventType == 4:
                if self.running:
                    self.pause()
            elif event.EventType == 7:
                if not self.running:
                    self.resume()

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkTimeTracker(root)
    root.mainloop()