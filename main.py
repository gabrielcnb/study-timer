import customtkinter
import os
import time
import math
import csv
import json
from datetime import datetime, timedelta
import tkinter
from tkinter import messagebox, simpledialog

# matplotlib is optional: without it the charts tab degrades gracefully
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# pystray and PIL are optional: they only power the system tray icon
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None


class StudyTimer:
    def __init__(self):
        # Appearance and theme
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")

        # Main window
        self.root = customtkinter.CTk()
        self.root.title("Study Timer & Statistics")
        self.root.geometry("500x600")
        self.root.minsize(500, 600)
        try:
            self.root.iconbitmap("app_icon.ico")  # expects an app_icon.ico next to this file
        except Exception as e:
            print("Icon not found:", e)

        # Timing and mode state
        self.daily_target = 60 * 60  # daily target in seconds (default: 60 min)
        self.pomodoro_mode = False
        self.in_break = False
        self.session_time = 0         # continuous mode
        self.focus_time = 0           # focus time in the current Pomodoro segment
        self.break_time = 0           # break time in the current Pomodoro segment
        self.total_focus = 0          # every focus stretch in the Pomodoro session
        self.running = False          # is a session active
        self.last_update = time.time()
        self.current_mode = "Continuous"  # or "Pomodoro"

        # Subjects offered to the user
        self.subjects = ["General", "Maths", "Portuguese", "English", "History", "Science"]
        self.current_subject = "General"

        # Session history CSV (created with a header if missing)
        self.history_file = "history.csv"
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["date", "subject", "duration", "mode"])

        # Tabbed interface
        self.tabview = customtkinter.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("Study")
        self.tabview.add("Reports")
        self.tabview.add("Settings")
        self.tab_study = self.tabview.tab("Study")
        self.tab_reports = self.tabview.tab("Reports")
        self.tab_config = self.tabview.tab("Settings")

        # ----------------------------
        # "Study" tab
        # ----------------------------
        # Timer label (session time, or focus/break time in Pomodoro mode)
        self.timer_label = customtkinter.CTkLabel(
            master=self.tab_study, text="Session: 00:00:00", font=("Arial", 24)
        )
        self.timer_label.pack(pady=10)

        # Progress towards the daily target
        self.progress_bar = customtkinter.CTkProgressBar(master=self.tab_study)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, fill="x", padx=20)

        # Subject picker
        self.subject_menu = customtkinter.CTkOptionMenu(
            master=self.tab_study, values=self.subjects, command=self.set_subject
        )
        self.subject_menu.set("General")
        self.subject_menu.pack(pady=10)

        # Start/pause the session
        self.toggle_button = customtkinter.CTkButton(
            master=self.tab_study, text="Start", command=self.toggle_pause
        )
        self.toggle_button.pack(pady=10)

        # Log hours by hand, for study done away from the app
        self.manual_button = customtkinter.CTkButton(
            master=self.tab_study, text="Log Manually", command=self.log_manual
        )
        self.manual_button.pack(pady=10)

        # Time spent per subject
        self.subject_stats_label = customtkinter.CTkLabel(
            master=self.tab_study, text="Time Spent per Subject:\n", font=("Arial", 12)
        )
        self.subject_stats_label.pack(pady=10)
        self.refresh_subject_stats()

        # ----------------------------
        # "Reports" tab
        # ----------------------------
        self.graph_button = customtkinter.CTkButton(
            master=self.tab_reports, text="Generate Chart", command=self.generate_chart
        )
        self.graph_button.pack(pady=10)

        self.history_button = customtkinter.CTkButton(
            master=self.tab_reports, text="Full History", command=self.show_history
        )
        self.history_button.pack(pady=10)

        self.stats_label = customtkinter.CTkLabel(
            master=self.tab_reports, text="Statistics: ", font=("Arial", 16)
        )
        self.stats_label.pack(pady=10)

        # ----------------------------
        # "Settings" tab
        # ----------------------------
        # Daily target in minutes
        self.label_target = customtkinter.CTkLabel(
            master=self.tab_config, text="Daily Target (min):", font=("Arial", 14)
        )
        self.label_target.pack(pady=5)
        self.entry_target = customtkinter.CTkEntry(master=self.tab_config, width=60)
        self.entry_target.insert(0, str(self.daily_target // 60))
        self.entry_target.pack(pady=5)
        self.btn_set_target = customtkinter.CTkButton(
            master=self.tab_config, text="Set Daily Target", command=self.set_daily_target
        )
        self.btn_set_target.pack(pady=5)

        # Pomodoro cycles
        self.label_pomodoro = customtkinter.CTkLabel(
            master=self.tab_config, text="Pomodoro Cycles:", font=("Arial", 14)
        )
        self.label_pomodoro.pack(pady=5)
        self.entry_pomodoro_cycles = customtkinter.CTkEntry(master=self.tab_config, width=60)
        self.entry_pomodoro_cycles.insert(0, "4")
        self.entry_pomodoro_cycles.pack(pady=5)

        # Theme picker
        self.label_theme = customtkinter.CTkLabel(
            master=self.tab_config, text="Theme:", font=("Arial", 14)
        )
        self.label_theme.pack(pady=5)
        self.themes = ["dark-blue", "green", "purple", "light"]
        self.option_theme = customtkinter.CTkOptionMenu(
            master=self.tab_config, values=self.themes, command=self.change_theme
        )
        self.option_theme.set("dark-blue")
        self.option_theme.pack(pady=5)

        # Pomodoro mode toggle
        self.toggle_pomodoro = customtkinter.CTkButton(
            master=self.tab_config, text="Enable Pomodoro Mode", command=self.toggle_pomodoro_mode
        )
        self.toggle_pomodoro.pack(pady=5)

        # Export history to JSON
        self.export_button = customtkinter.CTkButton(
            master=self.tab_config, text="Export Data (JSON)", command=self.export_data
        )
        self.export_button.pack(pady=5)

        # Simulated cloud backup
        self.backup_button = customtkinter.CTkButton(
            master=self.tab_config, text="Cloud Backup", command=self.cloud_backup
        )
        self.backup_button.pack(pady=5)

        # Add a new subject
        self.label_add_subject = customtkinter.CTkLabel(
            master=self.tab_config, text="Add Subject:", font=("Arial", 14)
        )
        self.label_add_subject.pack(pady=5)
        self.entry_add_subject = customtkinter.CTkEntry(master=self.tab_config, width=140)
        self.entry_add_subject.pack(pady=5)
        self.btn_add_subject = customtkinter.CTkButton(
            master=self.tab_config, text="Add", command=self.add_subject
        )
        self.btn_add_subject.pack(pady=5)

        # Minimise to the system tray, when pystray is available
        if pystray is not None:
            self.btn_tray = customtkinter.CTkButton(
                master=self.tab_config, text="Minimise to Tray", command=self.minimise_to_tray
            )
            self.btn_tray.pack(pady=5)

        # Tick the timer once a second
        self.update_timer()

        # Log the running session before the window closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def set_subject(self, value):
        self.current_subject = value

    # Start the session, or pause it and log the accumulated time
    def toggle_pause(self):
        if not self.running:
            self.running = True
            self.last_update = time.time()
            self.toggle_button.configure(text="Pause")
        else:
            if self.pomodoro_mode:
                duration = self.total_focus
                mode = "Pomodoro"
                self.total_focus = 0
                self.focus_time = 0
                self.break_time = 0
                self.in_break = False
            else:
                duration = self.session_time
                mode = "Continuous"
                self.session_time = 0
            if duration > 0:
                self.log_session(duration, mode)
            self.running = False
            self.toggle_button.configure(text="Start")

    # Tick once a second; in Pomodoro mode, derive focus/break from the target and cycles
    def update_timer(self):
        if self.running:
            current_time = time.time()
            elapsed = int(current_time - self.last_update)
            if elapsed >= 1:
                self.last_update = current_time
                if self.pomodoro_mode:
                    try:
                        cycles = int(self.entry_pomodoro_cycles.get())
                    except:
                        cycles = 4
                    if cycles < 1:
                        cycles = 1
                    # 90% of the target goes to focus, 10% to breaks
                    focus_interval = int(self.daily_target * 0.9 / cycles)
                    break_interval = int(self.daily_target * 0.1 / (cycles - 1)) if cycles > 1 else 0

                    if not self.in_break:
                        self.focus_time += elapsed
                        self.total_focus += elapsed
                        if self.focus_time >= focus_interval:
                            messagebox.showinfo("Pomodoro", f"Focus over. Starting a {break_interval//60} minute break.")
                            self.in_break = True
                            self.break_time = 0
                    else:
                        self.break_time += elapsed
                        if self.break_time >= break_interval:
                            messagebox.showinfo("Pomodoro", "Break over. Back to focus.")
                            self.in_break = False
                            self.focus_time = 0
                else:
                    self.session_time += elapsed

                if self.pomodoro_mode:
                    if self.in_break:
                        time_display = str(timedelta(seconds=self.break_time))
                        mode_text = "Break"
                    else:
                        time_display = str(timedelta(seconds=self.focus_time))
                        mode_text = "Focus"
                    self.timer_label.configure(text=f"{mode_text}: {time_display}")
                    progress = self.total_focus / self.daily_target
                else:
                    self.timer_label.configure(text="Session: " + str(timedelta(seconds=self.session_time)))
                    progress = self.session_time / self.daily_target

                progress = min(progress, 1)
                self.progress_bar.set(progress)
        self.root.after(1000, self.update_timer)

    # Append the session to the history CSV
    def log_session(self, duration, mode):
        with open(self.history_file, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([now, self.current_subject, duration, mode])

    # Log study time by hand, for sessions the timer never saw
    def log_manual(self):
        try:
            minutes = float(simpledialog.askstring("Manual Entry", "Minutes studied:"))
            duration = int(minutes * 60)
            self.log_session(duration, "Manual")
            messagebox.showinfo("Manual Entry", f"{minutes} minutes logged.")
        except Exception as e:
            messagebox.showerror("Error", "Invalid input.")

    def set_daily_target(self):
        try:
            minutes = float(self.entry_target.get())
            self.daily_target = int(minutes * 60)
            messagebox.showinfo("Daily Target", f"Daily target set to {minutes} minutes.")
        except Exception as e:
            messagebox.showerror("Error", "Please enter a valid number.")

    def change_theme(self, theme):
        customtkinter.set_default_color_theme(theme)
        messagebox.showinfo("Theme", f"Theme changed to {theme}.")

    def toggle_pomodoro_mode(self):
        self.pomodoro_mode = not self.pomodoro_mode
        if self.pomodoro_mode:
            self.toggle_pomodoro.configure(text="Disable Pomodoro Mode")
            self.current_mode = "Pomodoro"
            self.focus_time = 0
            self.break_time = 0
            self.total_focus = 0
            self.in_break = False
            messagebox.showinfo("Pomodoro", "Pomodoro mode enabled.\nFocus and break lengths come from the daily target and the number of cycles.")
        else:
            self.toggle_pomodoro.configure(text="Enable Pomodoro Mode")
            self.current_mode = "Continuous"
            messagebox.showinfo("Pomodoro", "Pomodoro mode disabled.")

    def export_data(self):
        if not os.path.exists(self.history_file):
            messagebox.showerror("Error", "History file not found.")
            return
        data = []
        with open(self.history_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        with open("history.json", "w") as jsonfile:
            json.dump(data, jsonfile, indent=4)
        messagebox.showinfo("Export Data", "Data exported to history.json.")

    # Placeholder: no cloud backend is wired up
    def cloud_backup(self):
        messagebox.showinfo("Backup", "Cloud backup completed (simulated).")

    # Chart the last seven days of study hours
    def generate_chart(self):
        if plt is None:
            messagebox.showerror("Error", "Matplotlib is not installed.")
            return

        data_agg = {}
        with open(self.history_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                date_str = row["date"].split(" ")[0]
                try:
                    duration = int(row["duration"])
                except:
                    continue
                data_agg[date_str] = data_agg.get(date_str, 0) + duration / 3600  # in hours

        if data_agg:
            dates = sorted(data_agg.keys())[-7:]
            hours = [data_agg[d] for d in dates]
        else:
            dates = []
            hours = []

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(dates, hours, color='skyblue')
        ax.set_title("Daily Study Hours")
        ax.set_ylabel("Hours")
        if hours:
            ax.set_ylim(0, max(hours + [self.daily_target / 3600, 1]))
        else:
            ax.set_ylim(0, self.daily_target / 3600 if self.daily_target > 0 else 1)

        total = self.total_studied() / 3600
        avg = sum(hours) / len(hours) if hours else 0
        if total < 10:
            level = "Beginner"
        elif total < 50:
            level = "Advanced"
        else:
            level = "Study master"
        self.stats_label.configure(
            text=f"Total Studied: {total:.2f}h | Average: {avg:.2f}h/day | Level: {level}"
        )

        top = customtkinter.CTkToplevel(self.root)
        top.title("Daily Study Chart")
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_history(self):
        top = customtkinter.CTkToplevel(self.root)
        top.title("Full History")
        txt = tkinter.Text(top, width=80, height=20)
        txt.pack()
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as csvfile:
                content = csvfile.read()
                txt.insert("end", content)
        else:
            txt.insert("end", "No records found.")

    # Total studied time in seconds, across the whole history
    def total_studied(self):
        total = 0
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        total += int(row["duration"])
                    except:
                        pass
        return total

    # Recompute per-subject totals and refresh the label every five seconds
    def refresh_subject_stats(self):
        subject_totals = {}
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        duration = int(row["duration"])
                    except:
                        duration = 0
                    subject = row["subject"]
                    subject_totals[subject] = subject_totals.get(subject, 0) + duration
        text = "Time Spent per Subject:\n"
        for subj, secs in subject_totals.items():
            text += f"{subj}: {str(timedelta(seconds=secs))}\n"
        self.subject_stats_label.configure(text=text)
        self.root.after(5000, self.refresh_subject_stats)

    def add_subject(self):
        new_subject = self.entry_add_subject.get().strip()
        if new_subject and new_subject not in self.subjects:
            self.subjects.append(new_subject)
            self.subject_menu.configure(values=self.subjects)
            messagebox.showinfo("Subject", f"Subject '{new_subject}' added.")
        else:
            messagebox.showerror("Error", "Invalid or duplicate subject.")

    def minimise_to_tray(self):
        self.root.withdraw()  # hide the main window
        if pystray is not None:
            image = self.build_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Open", self.show_window),
                pystray.MenuItem("Quit", self.quit_from_tray)
            )
            self.tray_icon = pystray.Icon("app", image, "Study Timer", menu)
            # pystray runs the icon on its own thread
            self.tray_icon.run()

    def build_tray_image(self):
        image = Image.new('RGB', (64, 64), color="black")
        dc = ImageDraw.Draw(image)
        dc.ellipse((0, 0, 64, 64), fill="blue")
        return image

    def show_window(self, icon, item):
        self.root.after(0, self.show_window_callback)

    def show_window_callback(self):
        self.root.deiconify()
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None

    def quit_from_tray(self, icon, item):
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.destroy()

    # Log whatever is running before shutting down
    def on_close(self):
        if self.running:
            if self.pomodoro_mode:
                duration = self.total_focus
            else:
                duration = self.session_time
            if duration > 0:
                mode = "Pomodoro" if self.pomodoro_mode else "Continuous"
                self.log_session(duration, mode)
        self.root.destroy()


if __name__ == "__main__":
    StudyTimer()
