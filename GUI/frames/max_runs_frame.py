# max_runs_frame.py
import tkinter as tk
from tkinter import ttk

from GUI.colours import GKN_BG, GKN_TEXT
# we assume your “TButton” style already uses GKN_PRIMARY/GKN_SECONDARY

class MaxRunsFrame(ttk.Frame):
    def __init__(self, master, app):
        # shrink the content region to 20% width
        app.set_content_size(0.2)
        super().__init__(master, style="TFrame")
        self.app = app

        # ─── HEADER BAR ─────────────────────────────────────────────────────────
        header = ttk.Frame(self, style="TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10,0))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Specify Max Runs",
            font=("Segoe UI", 12, "bold"),
            foreground=GKN_TEXT,
            background=GKN_BG
        ).grid(row=0, column=0, sticky="w", padx=10)

        ttk.Button(
            header,
            text="Next ▶",
            command=self.on_next,
            style="TButton"
        ).grid(row=0, column=1, sticky="e", padx=10)

        # ─── SCROLLABLE AREA ────────────────────────────────────────────────────
        container = ttk.Frame(self, style="TFrame")
        container.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10, padx=10)
        # allow the container to expand vertically
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        canvas    = tk.Canvas(container, bg=GKN_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas, style="TFrame")

        # put the scrollable frame in the canvas
        canvas.create_window((0,0), window=scrollable, anchor="nw")

        # configure scrolling
        canvas.configure(yscrollcommand=scrollbar.set)

        # grid them
        canvas .grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # allow canvas to expand
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # update scrollregion whenever the scrollable frame changes size
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable.bind("<Configure>", on_frame_configure)

        # also bind the mouse wheel
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
         "<MouseWheel>",
          lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units")
        ))
        # When mouse leaves, unbind the wheel
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ─── YOUR ENTRY ROWS ─────────────────────────────────────────────────────
        self.entries = {}
        for op in app.selected_ops:
            frm = ttk.Frame(scrollable, style="TFrame")
            frm.pack(fill="x", pady=2)

            ttk.Label(
                frm, text=op, width=25, anchor="w",
                background=GKN_BG, foreground=GKN_TEXT
            ).grid(row=0, column=0, sticky="w")

            ent = ttk.Entry(frm, width=10)
            ent.insert(0, "1")
            ent.grid(row=0, column=1, padx=5)

            self.entries[op] = ent

        # finally show this whole page
        self.pack(fill="both", expand=True)

    def on_next(self):
        max_runs = {}
        for op, ent in self.entries.items():
            try:
                max_runs[op] = int(ent.get())
            except ValueError:
                max_runs[op] = 1
        self.app.max_runs = max_runs

        # go to next frame
        self.destroy()
        from .run_params_frame import RunParamsFrame
        RunParamsFrame(self.master, self.app)
