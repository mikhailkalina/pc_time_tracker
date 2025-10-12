import pythoncom
import wmi
import threading
import time
import tkinter as tk
from tkinter import ttk
import json
import sys, os
import datetime
from datetime import date, timedelta

SAVE_FILE = "worktime_data.json"
WORK_SECONDS_PER_DAY = 4 * 3600

class WorkTimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Work Time Tracker")
        self.root.geometry("320x300")
        self.root.resizable(False, False)
        
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(app_path, "clock.ico")
        self.root.iconbitmap(icon_path)

        self.load_data()
        self.update_workdays()

        self.create_ui()
        self.resume()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Timer tick handler
        threading.Thread(target=self.update_timer, daemon=True).start()

        # WMI Sleep/Resume handler
        threading.Thread(target=self.watch_sleep_resume, daemon=True).start()

    def create_ui(self):
        self.work_time_label = ttk.Label(self.root, text="Work Time:", font=("Segoe UI", 14))
        self.work_time_label.pack(pady=5)

        self.work_time_value_label = ttk.Label(self.root, text=self.format_time(self.last_day_time), font=("Segoe UI", 20, "bold"))
        self.work_time_value_label.pack(pady=5)

        self.button = ttk.Button(self.root, text="Pause", command=self.toggle)
        self.button.pack(pady=15)
        
        self.score_label = ttk.Label(self.root, text="Score Time:", font=("Segoe UI", 12))
        self.score_label.pack()
        self.score_time_label = ttk.Label(self.root, text=self.format_time(0), font=("Segoe UI", 12, "bold"))
        self.score_time_label.pack()

        self.total_label = ttk.Label(self.root, text="Total Time:", font=("Segoe UI", 10))
        self.total_label.pack()
        self.total_time_label = ttk.Label(self.root, text=self.format_time(self.total_time), font=("Segoe UI", 10, "bold"))
        self.total_time_label.pack()

        self.date_label = ttk.Label(self.root, text="Work Date:", font=("Segoe UI", 10))
        self.date_label.pack()
        self.last_day_date_label = ttk.Label(self.root, text=self.last_day_date, font=("Segoe UI", 10, "bold"))
        self.last_day_date_label.pack()

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.resume()

    def pause(self):
        self.running = False
        self.last_day_time += self.elapsed_running_time
        self.save_data()
        self.button.config(text="Resume")

    def resume(self):
        self.running = True
        self.elapsed_running_time = int(0)
        self.start_running_time = time.time()
        if self.last_day_date != datetime.date.today().isoformat():
            self.on_new_date()
        self.button.config(text="Pause")

    def on_new_date(self):
        self.last_day_time += self.elapsed_running_time
        self.elapsed_running_time = int(0)
        self.start_running_time = time.time()
        # Update total time
        self.total_time += self.last_day_time
        self.total_time_label.config(text=self.format_time(self.total_time))
        # Clear day time
        self.last_day_time = 0
        self.work_time_value_label.config(text=self.format_time(self.last_day_time))
        # Update lat date
        self.last_day_date = datetime.date.today().isoformat()
        self.last_day_date_label.config(text=self.last_day_date)
        # Save new data
        self.save_data()
        # Updated workdays and score time
        self.update_workdays()
        self.update_score_time()

    def on_close(self):
        if self.running:
            self.pause()
        self.root.destroy()

    def format_time(self, seconds):
        sign = "-" if seconds < 0 else ""
        seconds = abs(seconds)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{sign}{h:02}:{m:02}:{s:02}"
        
    def update_score_time(self):
        score_time = self.total_time + self.last_day_time + self.elapsed_running_time - self.workdays * WORK_SECONDS_PER_DAY
        self.score_time_label.config(text=self.format_time(score_time))
        if score_time >= 0:
            self.score_time_label.config(foreground="green")
        else:
            self.score_time_label.config(foreground="red")

    def update_workdays(self):
        current = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end_date = date.today()
        self.workdays = 0
        while current <= end_date:
            if current.weekday() < 5:
                self.workdays += 1
            current += timedelta(days=1)

    def save_data(self):
        data = {"last_day_date": self.last_day_date,
                "last_day_time": int(self.last_day_time),
                "total_time": int(self.total_time),
                "start_date": self.start_date}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                self.last_day_date = data.get("last_day_date", 0)
                self.last_day_time = int(data.get("last_day_time", 0))
                self.total_time = int(data.get("total_time", 0))
                self.start_date = data.get("start_date", datetime.date.today().isoformat())
        else:
            self.last_day_date = 0
            self.last_day_time = int(0)
            self.total_time = int(0)
            self.start_date = datetime.date.today().isoformat()

    # ---------------- Time tick ----------------
    def update_timer(self):
        while True:
            if self.last_day_date != datetime.date.today().isoformat():
                self.on_new_date()
            if self.running:
                self.elapsed_running_time = int(time.time() - self.start_running_time)
                work_time = self.last_day_time + self.elapsed_running_time
                self.work_time_value_label.config(text=self.format_time(work_time))
                self.update_score_time()
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