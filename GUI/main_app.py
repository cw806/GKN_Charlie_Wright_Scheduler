# main_app.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from Scheduler.load_data import load_data
from Scheduler.model import solve_throughput_with_earliest
from .frames.initial_frame import InitialFrame
from .colours import GKN_BG, GKN_PRIMARY, GKN_SECONDARY, GKN_TEXT
import sys
import os

# planning horizon default
default_horizon = 22 * 60
# ─── SPLASH SCREEN ────────────────────────────────────────────────────────────
class Splash(tk.Toplevel):
    def __init__(self, parent, img_path):
        super().__init__(parent)
        self.overrideredirect(True)       # no window decorations
        self.attributes('-topmost', True) # stay on top

        # Load the same background image
        self.bg = tk.PhotoImage(file=img_path)
        lbl = tk.Label(self, image=self.bg)
        lbl.pack(fill="both", expand=True)

        # “Loading…” text
        self.msg = tk.Label(self, text="Loading Scheduler…", 
                            font=("Segoe UI",12,"bold"), bg=GKN_TEXT, fg=GKN_BG)
        self.msg.place(relx=0.5, rely=0.9, anchor="center")

        # Center on screen
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


class MainApp(ThemedTk):
    def __init__(self):
        # 1) create the real root first
        super().__init__(theme="arc")

        # 2) now you can safely load images into that root
        script_dir = os.path.dirname(__file__)
        bg_path = os.path.abspath(os.path.join(script_dir, '..', 'data', 'background.png'))
        self.bg_image = tk.PhotoImage(file=bg_path)

        # 3) show a splash on top of this root
        splash = Splash(self, bg_path)
        splash.update()

        # Fullscreen
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', True)
            
        splash.destroy()

        # Style configuration
        style = ttk.Style(self)
        style.theme_use("arc")
        style.configure("TFrame", background=GKN_BG)
        style.configure("TLabel", background=GKN_BG, foreground=GKN_SECONDARY)
        style.configure("TButton", background=GKN_PRIMARY, foreground=GKN_SECONDARY,
                        font=("Segoe UI", 10, 'bold'))
        style.map("TButton", background=[('active', GKN_SECONDARY)])

        # Window title & background
        self.title("Scheduler Simulator")
        self.configure(bg=GKN_BG)

        # Background image
        script_dir = os.path.dirname(__file__)
        bg_path = os.path.abspath(os.path.join(script_dir, '..', 'data', 'background.png'))
        self.bg_image = tk.PhotoImage(file=bg_path)
        bg_lbl = tk.Label(self, image=self.bg_image)
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        # Global attributes for frames
        self.program_start_minutes = 7 * 60
        self.show_simulation       = True
        self.show_gantt            = True

        # Load data
        self.sd, self.ops = load_data()
        self.station_caps = {st: 1 for st in self.sd if st not in ('S', 'FIN')}

        # Content container
        self.content = ttk.Frame(self, style="TFrame")
        self.content.place(
            relx=0.5, rely=0.5, anchor="center",
            relwidth=0.75, relheight=0.75
        )

        # Helper for resizing content
        def set_content_size(w):
            self.content.place_configure(relwidth=w)
        self.set_content_size = set_content_size

        # Kick off initial page
        InitialFrame(self.content, self)

        # Status bar
        status = ttk.Label(
            self,
            relief="sunken",
            anchor="w",
            text="Ready",
            background=GKN_BG,
            foreground=GKN_TEXT
        )
        status.pack(fill="x", side="bottom")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == '__main__':
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
