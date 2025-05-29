# frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from .controls import ControlPanel
from .sim_canvas import SimulationCanvas
from .gantt_canvas import GanttCanvas
from .animation import Animator
from .utils import preprocess_schedule, format_time_for_axis
import pandas as pd
import os

class ScheduleFrame(tk.Frame):
    def __init__(self, master, sched, tasks, sd, makespan,
                 selected_ops, ops, weights, max_runs):
        super().__init__(master)
        # Store for export
        self.sched = sched
        self.tasks = tasks
        self.selected_ops = selected_ops
        self.ops = ops
        self.weights = weights
        self.max_runs = max_runs
        # Store earliest & program start
        self.earliest     = master.winfo_toplevel().earliest
        self.base_minutes = master.winfo_toplevel().program_start_minutes

        # Prepare schedule data
        data = preprocess_schedule(sched, tasks, sd, makespan)
        data.selected_ops = selected_ops
        data.ops           = ops
        data.weights       = weights
        data.max_runs      = max_runs
        data.base_minutes  = self.base_minutes
        data.formatter     = format_time_for_axis(self.base_minutes)

        # Controls panel first
        self.anim     = Animator(self, data)
        self.controls = ControlPanel(self, data)

        # Then canvases
        self.sim   = SimulationCanvas(self, data)
        self.gantt = GanttCanvas(self, data)

        # Layout and start
        self.pack(fill="both", expand=True)
        self.anim.start()

    def _minutes_to_clock(self, minutes):
        hh = int(minutes // 60) % 24
        mm = int(minutes % 60)
        return f"{hh:02d}:{mm:02d}"

    def export_to_excel(self):
        base_file = "schedule_output"
        counter = 0
        while True:
            file_path = f"{base_file}{'' if counter==0 else f'_{counter}'}.xlsx"
            if not os.path.exists(file_path):
                break
            counter += 1

        # Build schedule rows
        rows = []
        for jid in sorted({j for j,_ in self.sched}):
            op = jid.rsplit('_',1)[0]
            ivs = [(s,e) for (j,i),(s,e) in self.sched.items() if j==jid and self.tasks[(j,i)]['type']=='PROCESS']
            entry = min((s for s,e in ivs), default=0)
            exit_ = max((e for s,e in ivs), default=0)
            rows.append({
                'Job ID': jid,
                'Weight': self.weights.get(op, 1.0),
                'Entry (min)': entry,
                'Entry (clock)': self._minutes_to_clock(self.base_minutes+entry),
                'Exit (min)': exit_,
                'Exit (clock)': self._minutes_to_clock(self.base_minutes+exit_)
            })
        df = pd.DataFrame(rows)

        # Write single sheet
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name='Schedule', index=False)
        messagebox.showinfo('Export', f'Schedule exported to {file_path}')

    def show_timings(self):
        messagebox.showinfo('Timings', 'Not yet implemented')

    def toggle_gantt_fullscreen(self):
        if self.sim.winfo_viewable():
            self.sim.pack_forget()
        else:
            self.sim.pack(side="top", fill="both", expand=False)
