import tkinter as tk
from tkinter import filedialog, messagebox, StringVar, OptionMenu, Frame, Label, Button, Listbox, Checkbutton, Entry
import shutil  # Library for file operations, including copying
import os  # Library for operating system related functions
import configparser  # Library for reading and writing configuration files
import time  # Library for time-related functions
import threading  # Library for running tasks in separate threads
import pystray  # Library for creating system tray icons
from pystray import MenuItem, Icon  # Required components for tray icon
from PIL import Image, ImageDraw  # Library for creating images

class FileCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Copy Files")  # Set the window title
        self.root.geometry("600x500")  # Set the window size
        self.root.configure(bg="#f0f0f0")  # Set the background color

        # Configuration of the settings file to store user preferences
        self.config_file = 'Auto_Copy_Files.json'

        # List of time options for the timer
        self.time_options = [
            "5 sec", "1 min", "5 min", "30 min",
            "1 hour", "12 hour"
        ]
        self.selected_time = StringVar()  # Variable to hold the selected time option
        self.load_settings()  # Load previously saved settings if available

        # Frame for selecting source folders
        self.source_frame = Frame(root, bg="#f0f0f0")
        self.source_frame.pack(pady=10)  # Position the frame with padding

        # Label to indicate the purpose of the source_frame
        self.source_label = Label(self.source_frame, text="Source Folders:", bg="#f0f0f0", font=("Arial", 12))
        self.source_label.pack(side=tk.LEFT)

        # Listbox to display and select source folders
        self.source_listbox = Listbox(self.source_frame, width=40, height=10, selectmode=tk.MULTIPLE)
        self.source_listbox.pack(side=tk.LEFT, padx=(10, 0))  # Add padding

        # Button to add source folders
        self.add_source_button = Button(self.source_frame, text="Add Source", command=self.add_source_folder, bg="#4CAF50", fg="white")
        self.add_source_button.pack(side=tk.LEFT, padx=(10, 0))

        # Button to remove selected source folders from the list
        self.remove_source_button = Button(self.source_frame, text="Remove Selected", command=self.remove_selected_source, bg="#F44336", fg="white")
        self.remove_source_button.pack(side=tk.LEFT, padx=(5, 0))

        # Frame for choosing the destination folder
        self.destination_frame = Frame(root, bg="#f0f0f0")
        self.destination_frame.pack(pady=10)

        # Label for the destination folder input
        self.destination_label = Label(self.destination_frame, text="Destination Folder:", bg="#f0f0f0", font=("Arial", 12))
        self.destination_label.pack(side=tk.LEFT)

        # Entry field for the destination folder path
        self.destination_entry = Entry(self.destination_frame, width=40)
        self.destination_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Button to browse and select a destination folder
        self.browse_dest_button = Button(self.destination_frame, text="Browse", command=self.browse_destination_folder, bg="#2196F3", fg="white")
        self.browse_dest_button.pack(side=tk.LEFT, padx=(5, 0))

        # Frame for timer settings
        self.timer_frame = Frame(root, bg="#f0f0f0")
        self.timer_frame.pack(pady=10)

        # Label for the timer settings
        self.timer_label = Label(self.timer_frame, text="Time (seconds):", bg="#f0f0f0", font=("Arial", 12))
        self.timer_label.pack(side=tk.LEFT)

        # Dropdown menu for selecting default time from the list of options
        self.selected_time.set(self.time_options[0])  # Default selection
        self.time_dropdown = OptionMenu(self.timer_frame, self.selected_time, *self.time_options, command=self.update_timer_entry)
        self.time_dropdown.pack(side=tk.LEFT, padx=(10, 0))

        # Entry for manual time input
        self.timer_entry = Entry(self.timer_frame, width=10)
        self.timer_entry.insert(0, str(self.timer_seconds))  # Set initial value
        self.timer_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Button to start or stop the copy process
        self.start_button = Button(self.timer_frame, text="Start/Stop Copy", command=self.toggle_copying, bg="#FF9800", fg="white")
        self.start_button.pack(side=tk.LEFT, padx=(10, 0))

        # Label to display countdown for the next copy
        self.countdown_label = Label(root, text="", bg="#f0f0f0", font=("Arial", 14))
        self.countdown_label.pack(pady=10)

        # Checkbox option to show a success message after copying files
        self.message_option_var = tk.BooleanVar(value=self.show_success_message)
        self.message_option = Checkbutton(root, text="Show Success Message", variable=self.message_option_var, bg="#f0f0f0")
        self.message_option.pack(pady=5)

        # Checkbox to enable auto-start of the copying process when launching the app
        self.auto_start_var = tk.BooleanVar(value=self.auto_start)
        self.auto_start_option = Checkbutton(root, text="Auto-start at tool launch", variable=self.auto_start_var, bg="#f0f0f0")
        self.auto_start_option.pack(pady=5)

        # Checkbox to enable immediate execution of the copy process
        self.immediate_execution_var = tk.BooleanVar(value=False)
        self.immediate_execution_option = Checkbutton(root, text="Execute copy immediately on start", variable=self.immediate_execution_var, bg="#f0f0f0")
        self.immediate_execution_option.pack(pady=5)

        # Initialize variables to track state
        self.source_dirs = []  # List to store source directories
        self.is_running = False  # Flag to indicate if the copying process is active
        self.start_time = None  # Variable to record the start time of the countdown
        self.end_time = None  # Variable to record the end time of the countdown

        # Load previously saved source folders and the destination folder from the settings
        self.load_saved_source_folders()
        self.load_destination_folder()

        # Automatically start the copying process if the auto-start option is enabled
        if self.auto_start:
            self.toggle_copying()

        # Setup for tray icon functionality
        self.tray_icon = None

    def load_settings(self):
        # Load saved settings from the configuration file
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)  # Read the config file if it exists
            # Load saved timer seconds with a fallback default
            self.timer_seconds = int(config.get("Settings", "timer_seconds", fallback="300"))
            self.show_success_message = config.getboolean("Settings", "show_success_message", fallback=True)
            self.auto_start = config.getboolean("Settings", "auto_start", fallback=False)
            # Load the selected time with a fallback default option
            self.selected_time.set(config.get("Settings", "selected_time", fallback=self.time_options[0]))
        else:
            # Default settings if the config file does not exist
            self.timer_seconds = 300
            self.show_success_message = True
            self.auto_start = False

    def save_settings(self):
        # Save current settings to the configuration file
        config = configparser.ConfigParser()
        config["Settings"] = {
            "timer_seconds": self.timer_entry.get(),  # Save the timer value
            "selected_time": self.selected_time.get(),  # Save the selected time
            "destination_folder": self.destination_entry.get(),  # Save the destination folder path
            "show_success_message": str(self.message_option_var.get()),  # Save message option state
            "auto_start": str(self.auto_start_var.get()),  # Save auto-start option state
            "source_folders": ','.join(self.source_dirs)  # Save source folders as a comma-separated string
        }
        with open(self.config_file, "w") as configfile:
            config.write(configfile)  # Write the settings to the config file

    def load_saved_source_folders(self):
        # Load previously saved source folders from the configuration file
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)  # Read the config file if it exists
            source_folders = config.get("Settings", "source_folders", fallback="")
            self.source_dirs = source_folders.split(',') if source_folders else []  # Split the string to list if not empty
            self.update_source_listbox()  # Update the visible list of source folders

    def load_destination_folder(self):
        # Load the saved destination folder path from the configuration file
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)  # Read the config file if it exists
            destination_folder = config.get("Settings", "destination_folder", fallback="")
            self.destination_entry.insert(0, destination_folder)  # Insert destination folder into entry field

    def update_timer_entry(self, value):
        # Update the manual entry field based on the selected dropdown time option
        conversions = {
            "5 sec": 5,
            "1 min": 60,
            "5 min": 300,
            "30 min": 1800,
            "1 hour": 3600,
            "12 hour": 43200,
        }
        self.timer_entry.delete(0, tk.END)  # Clear existing entry
        self.timer_entry.insert(0, str(conversions[value]))  # Set the related seconds in entry

    def add_source_folder(self):
        # Open file dialog to select a source folder and add it to the list
        folder = filedialog.askdirectory()
        if folder:  # Check if a folder was selected
            self.source_dirs.append(folder)  # Add folder to source directory list
            self.update_source_listbox()  # Update the Listbox to display the new source folder

    def remove_selected_source(self):
        # Remove selected folders from the Listbox
        selected_indices = self.source_listbox.curselection()  # Get the selected indices
        for index in reversed(selected_indices):  # Iterate over selected indices in reverse to avoid index shifting
            del self.source_dirs[index]  # Remove the folder from the source directory list
        self.update_source_listbox()  # Update the Listbox to reflect changes

    def update_source_listbox(self):
        # Clear and update the Listbox with current source directories
        self.source_listbox.delete(0, tk.END)  # Clear the Listbox
        for folder in self.source_dirs:
            self.source_listbox.insert(tk.END, folder)  # Insert each source folder into the Listbox

    def browse_destination_folder(self):
        # Open file dialog to select a destination folder
        folder = filedialog.askdirectory()
        if folder:  # Check if a folder was selected
            self.destination_entry.delete(0, tk.END)  # Clear existing entry
            self.destination_entry.insert(0, folder)  # Set the selected folder as the destination

    def toggle_copying(self):
        # Start or stop the copying process based on the current state
        if self.is_running:
            self.is_running = False  # Stop the copying process
            self.start_button.config(text="Start Copy")  # Update button text
        else:
            self.is_running = True  # Start the copying process
            self.start_button.config(text="Stop Copy")  # Update button text
            if self.immediate_execution_var.get():  # Check if immediate execution is enabled
                self.execute_copying()  # Execute copying immediately
            self.start_countdown()  # Start the countdown timer

    def start_countdown(self):
        # Start the countdown for the time specified in the timer entry
        try:
            self.start_time = time.time()  # Record the current time
            self.end_time = self.start_time + int(self.timer_entry.get())  # Set end time based on timer entry
            self.update_countdown()  # Begin updating the countdown
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the timer.")  # Handle invalid entries

    def update_countdown(self):
        # Update the countdown display and execute copying when time is up
        if self.is_running:
            remaining_time = int(self.end_time - time.time())  # Calculate remaining time
            if remaining_time > 0:
                self.countdown_label.config(text=f"Next copy in: {remaining_time} seconds")  # Update countdown label
                self.root.after(1000, self.update_countdown)  # Update again after 1 second
            else:
                self.execute_copying()  # Time is up, execute the copying process

    def execute_copying(self):
        # Perform the file copying operation from source directories to the destination folder
        destination = self.destination_entry.get()  # Get the destination folder
        if not os.path.exists(destination):
            os.makedirs(destination)  # Create destination folder if it does not exist

        for src_dir in self.source_dirs:  # Loop through each source directory
            for root, dirs, files in os.walk(src_dir):  # Walk through the directory tree
                for file in files:  # Loop through each file in the directory
                    src_file_path = os.path.join(root, file)  # Get the full source file path
                    relative_path = os.path.relpath(src_file_path, src_dir)  # Calculate the relative path
                    dest_file_path = os.path.join(destination, relative_path)  # Construct the destination file path

                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)  # Create directory for destination file
                    shutil.copy2(src_file_path, dest_file_path)  # Copy the file to the destination

        if self.message_option_var.get(): 
            messagebox.showinfo("Success", "Files copied successfully!")  # Show success message if enabled

        if self.is_running:
            self.start_countdown()  # Restart countdown for the next copy cycle

    def on_closing(self):
        # Handle the closing event to save settings before exiting
        self.save_settings()  # Save current settings
        self.root.destroy()  # Destroy the application window

    def minimize_to_tray(self):
        # Minimize the application to the system tray
        self.root.withdraw()  # Hide the main window
        self.show_tray_icon()  # Display the tray icon

    def show_tray_icon(self):
        # Create and display a tray icon with options
        image = Image.new('RGB', (64, 64), (255, 255, 255))  # Create an image for the icon
        dc = ImageDraw.Draw(image)  # Create a draw object
        dc.ellipse((16, 16, 48, 48), fill=(0, 128, 255))  # Draw a circle in the icon

        self.tray_icon = Icon("FileCopy", image)  # Create the tray icon
        self.tray_icon.menu = pystray.Menu(  # Create a menu for the tray icon
            MenuItem("Restore", self.restore_window),  # Option to restore the window
            MenuItem("Exit", self.exit_app)  # Option to exit the application
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()  # Run the tray icon in a separate thread

    def restore_window(self, icon):
        # Restore the application window from the tray
        icon.stop()  # Stop the tray icon
        self.root.deiconify()  # Show the main window

    def exit_app(self, icon=None):
        # Exit the application and save settings
        if icon:
            icon.stop()  # Stop the tray icon if it exists
        self.save_settings()  # Save settings before exit
        self.root.quit()  # Close the application

if __name__ == "__main__":
    root = tk.Tk()  # Create the main application window
    app = FileCopyApp(root)  # Instantiate the application
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Handle window close event
    root.bind("<Unmap>", lambda event: app.minimize_to_tray() if root.state() == "iconic" else None)  # Minimize to tray on close
    root.mainloop()  # Start the Tkinter event loop