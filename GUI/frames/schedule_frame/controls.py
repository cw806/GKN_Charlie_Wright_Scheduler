# controls.py
import tkinter as tk
from tkinter import ttk

class ControlPanel(ttk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.data   = data
        self.build()
        # pack controls at top
        self.pack(side="top", fill="x", pady=5)

    def build(self):
        ctl = ttk.Frame(self)
        ctl.pack(fill="x", padx=5, pady=5)

        # Clock label
        clk = ttk.Label(ctl, text="00:00", width=8)
        clk.pack(side="left", padx=(0,10))
        self.data.update_clock_label = lambda t: clk.config(text=self.data.formatter(t, None))

        # Buttons
        btns = [
            ("Play ▶",  self.parent.anim.play),
            ("Pause ■", self.parent.anim.pause),
            ("Export",  self.parent.export_to_excel),
            ("Timings", self.parent.show_timings),
        ]
        for txt, cmd in btns:
            tk.Button(ctl, text=txt, command=cmd).pack(side="left", padx=5)

        # Slider
        sld = tk.Scale(
            ctl, from_=0, to=self.data.makespan,
            orient='horizontal', resolution=0.5,
            command=lambda v: self.parent.anim.seek(float(v))
        )
        sld.pack(side="left", fill="x", expand=True, padx=5)
        self.data.slider = sld