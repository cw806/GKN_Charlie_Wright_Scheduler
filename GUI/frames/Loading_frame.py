from threading import Thread
from tkinter import ttk
import tkinter as tk

class LoadingWindow:
    def __init__(self, parent, message="Calculating schedule...\nPlease wait"):
        self.top = tk.Toplevel(parent)
        self.top.title("Processing")
        
        # Make window stay on top
        self.top.transient(parent)
        self.top.grab_set()
        
        # Center the window
        w = 300
        h = 100
        ws = parent.winfo_screenwidth()
        hs = parent.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.top.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        
        # Configure window
        self.top.resizable(False, False)
        self.top.configure(bg='white')
        
        # Add widgets
        self.label = ttk.Label(
            self.top,
            text=message,
            style='Loading.TLabel'
        )
        self.label.pack(pady=10)
        
        self.progress = ttk.Progressbar(
            self.top,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start(10)  # Speed up animation
        
        # Prevent window from being closed
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def update_message(self, message):
        """Update the loading message"""
        self.label.configure(text=message)
        self.top.update()
        
    def destroy(self):
        """Safely destroy the loading window"""
        self.progress.stop()
        self.top.grab_release()
        self.top.destroy()

