import tkinter as tk
from tkinter import filedialog, messagebox, StringVar, OptionMenu, Frame, Label, Button, Listbox, Checkbutton, Entry
import shutil
import os
import configparser
import time
import threading
import pystray
from pystray import MenuItem, Icon
from PIL import Image, ImageDraw


class FileCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Copy Files")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        # Configuration of the settings file
        self.config_file = 'Auto_Copy_Files.json'

        # Initialization of time_options and selected_time
        self.time_options = [
            "5 sec", "1 min", "5 min", "30 min",
            "1 hour", "12 hour"
        ]
        self.selected_time = StringVar()
        self.load_settings()

        # Frame for selecting source folders
        self.source_frame = Frame(root, bg="#f0f0f0")
        self.source_frame.pack(pady=10)

        self.source_label = Label(self.source_frame, text="Source Folders:", bg="#f0f0f0", font=("Arial", 12))
        self.source_label.pack(side=tk.LEFT)

        self.source_listbox = Listbox(self.source_frame, width=40, height=10, selectmode=tk.MULTIPLE)
        self.source_listbox.pack(side=tk.LEFT, padx=(10, 0))

        self.add_source_button = Button(self.source_frame, text="Add Source", command=self.add_source_folder, bg="#4CAF50", fg="white")
        self.add_source_button.pack(side=tk.LEFT, padx=(10, 0))

        self.remove_source_button = Button(self.source_frame, text="Remove Selected", command=self.remove_selected_source, bg="#F44336", fg="white")
        self.remove_source_button.pack(side=tk.LEFT, padx=(5, 0))

        # Frame for the destination folder
        self.destination_frame = Frame(root, bg="#f0f0f0")
        self.destination_frame.pack(pady=10)

        self.destination_label = Label(self.destination_frame, text="Destination Folder:", bg="#f0f0f0", font=("Arial", 12))
        self.destination_label.pack(side=tk.LEFT)

        self.destination_entry = Entry(self.destination_frame, width=40)
        self.destination_entry.pack(side=tk.LEFT, padx=(10, 0))

        self.browse_dest_button = Button(self.destination_frame, text="Browse", command=self.browse_destination_folder, bg="#2196F3", fg="white")
        self.browse_dest_button.pack(side=tk.LEFT, padx=(5, 0))

        # Frame for timer and countdown
        self.timer_frame = Frame(root, bg="#f0f0f0")
        self.timer_frame.pack(pady=10)

        self.timer_label = Label(self.timer_frame, text="Time (seconds):", bg="#f0f0f0", font=("Arial", 12))
        self.timer_label.pack(side=tk.LEFT)

        # Dropdown menu for selecting default time
        self.selected_time.set(self.time_options[0])  # Default value
        self.time_dropdown = OptionMenu(self.timer_frame, self.selected_time, *self.time_options, command=self.update_timer_entry)
        self.time_dropdown.pack(side=tk.LEFT, padx=(10, 0))

        # Entry for manual input
        self.timer_entry = Entry(self.timer_frame, width=10)
        self.timer_entry.insert(0, str(self.timer_seconds))
        self.timer_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.start_button = Button(self.timer_frame, text="Start/Stop Copy", command=self.toggle_copying, bg="#FF9800", fg="white")
        self.start_button.pack(side=tk.LEFT, padx=(10, 0))

        self.countdown_label = Label(root, text="", bg="#f0f0f0", font=("Arial", 14))
        self.countdown_label.pack(pady=10)

        # Checkbox to enable/disable the message
        self.message_option_var = tk.BooleanVar(value=self.show_success_message)
        self.message_option = Checkbutton(root, text="Show Success Message", variable=self.message_option_var, bg="#f0f0f0")
        self.message_option.pack(pady=5)

        # Checkbox for auto-start when the tool starts
        self.auto_start_var = tk.BooleanVar(value=self.auto_start)
        self.auto_start_option = Checkbutton(root, text="Auto-start at tool launch", variable=self.auto_start_var, bg="#f0f0f0")
        self.auto_start_option.pack(pady=5)

        # Checkbox for immediate execution
        self.immediate_execution_var = tk.BooleanVar(value=False)
        self.immediate_execution_option = Checkbutton(root, text="Execute copy immediately on start", variable=self.immediate_execution_var, bg="#f0f0f0")
        self.immediate_execution_option.pack(pady=5)

        self.source_dirs = []
        self.is_running = False
        self.start_time = None
        self.end_time = None

        # Load saved source folders
        self.load_saved_source_folders()
        self.load_destination_folder()

        # Auto-start the copier if selected
        if self.auto_start:
            self.toggle_copying()

        # Tray icon setup
        self.tray_icon = None

    def load_settings(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.timer_seconds = int(config.get("Settings", "timer_seconds", fallback="300"))
            self.show_success_message = config.getboolean("Settings", "show_success_message", fallback=True)
            self.auto_start = config.getboolean("Settings", "auto_start", fallback=False)
            self.selected_time.set(config.get("Settings", "selected_time", fallback=self.time_options[0]))
        else:
            self.timer_seconds = 300
            self.show_success_message = True
            self.auto_start = False

    def save_settings(self):
        config = configparser.ConfigParser()
        config["Settings"] = {
            "timer_seconds": self.timer_entry.get(),
            "selected_time": self.selected_time.get(),
            "destination_folder": self.destination_entry.get(),
            "show_success_message": str(self.message_option_var.get()),
            "auto_start": str(self.auto_start_var.get()),
            "source_folders": ','.join(self.source_dirs)
        }
        with open(self.config_file, "w") as configfile:
            config.write(configfile)

    def load_saved_source_folders(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            source_folders = config.get("Settings", "source_folders", fallback="")
            self.source_dirs = source_folders.split(',') if source_folders else []
            self.update_source_listbox()

    def load_destination_folder(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            destination_folder = config.get("Settings", "destination_folder", fallback="")
            self.destination_entry.insert(0, destination_folder)

    def update_timer_entry(self, value):
        conversions = {
            "5 sec": 5,
            "1 min": 60,
            "5 min": 300,
            "30 min": 1800,
            "1 hour": 3600,
            "12 hour": 43200,
        }
        self.timer_entry.delete(0, tk.END)
        self.timer_entry.insert(0, str(conversions[value]))

    def add_source_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_dirs.append(folder)
            self.update_source_listbox()

    def remove_selected_source(self):
        selected_indices = self.source_listbox.curselection()
        for index in reversed(selected_indices):
            del self.source_dirs[index]
        self.update_source_listbox()

    def update_source_listbox(self):
        self.source_listbox.delete(0, tk.END)
        for folder in self.source_dirs:
            self.source_listbox.insert(tk.END, folder)

    def browse_destination_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.destination_entry.delete(0, tk.END)
            self.destination_entry.insert(0, folder)

    def toggle_copying(self):
        if self.is_running:
            self.is_running = False
            self.start_button.config(text="Start Copy")
        else:
            self.is_running = True
            self.start_button.config(text="Stop Copy")
            if self.immediate_execution_var.get():
                self.execute_copying()
            self.start_countdown()

    def start_countdown(self):
        try:
            self.start_time = time.time()
            self.end_time = self.start_time + int(self.timer_entry.get())
            self.update_countdown()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the timer.")

    def update_countdown(self):
        if self.is_running:
            remaining_time = int(self.end_time - time.time())
            if remaining_time > 0:
                self.countdown_label.config(text=f"Next copy in: {remaining_time} seconds")
                self.root.after(1000, self.update_countdown)
            else:
                self.execute_copying()

    def execute_copying(self):
        destination = self.destination_entry.get()
        if not os.path.exists(destination):
            os.makedirs(destination)

        for src_dir in self.source_dirs:
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    src_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(src_file_path, src_dir)
                    dest_file_path = os.path.join(destination, relative_path)

                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                    shutil.copy2(src_file_path, dest_file_path)

        if self.message_option_var.get():
            messagebox.showinfo("Success", "Files copied successfully!")

        if self.is_running:
            self.start_countdown()  # Restart the countdown for the next copy cycle

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def minimize_to_tray(self):
        self.root.withdraw()
        self.show_tray_icon()

    def show_tray_icon(self):
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(0, 128, 255))

        self.tray_icon = Icon("FileCopy", image)
        self.tray_icon.menu = pystray.Menu(
            MenuItem("Restore", self.restore_window),
            MenuItem("Exit", self.exit_app)
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_window(self, icon):
        icon.stop()
        self.root.deiconify()

    def exit_app(self, icon=None):
        if icon:
            icon.stop()
        self.save_settings()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.bind("<Unmap>", lambda event: app.minimize_to_tray() if root.state() == "iconic" else None)
    root.mainloop()
