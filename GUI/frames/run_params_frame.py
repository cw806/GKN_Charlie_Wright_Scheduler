# run_params_frame.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from GUI.frames.Loading_frame import LoadingWindow
from GUI.colours import GKN_BG, GKN_SECONDARY
from Scheduler.model import solve_throughput_with_earliest
from Data.universal_variable import DEFAULT_HORIZON as default_horizon
from GUI.frames.schedule_frame.frame import ScheduleFrame
from threading import Thread


class RunParamsFrame(ttk.Frame):
    def __init__(self, master, app):
        # shrink content width to 20%
        app.set_content_size(0.5)
        super().__init__(master, style="TFrame")
        self.app = app

        # ─── HEADER BAR ──────────────────────────────────────────────────────────
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", pady=10)

        ttk.Label(
            header,
            text="Run Parameters",
            font=("Segoe UI", 12, "bold"),
            background=GKN_BG,
            foreground=GKN_SECONDARY
        ).pack(side="left", padx=(10,0))

        # Run ▶ button on the right, uses your TButton style
        ttk.Button(
            header,
            text="Run ▶",
            command=self.on_run,
            style="TButton"
        ).pack(side="right", padx=(0,10))

        # ─── SCROLLABLE PARAMETER GRID ──────────────────────────────────────────
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=(0,10))

        canvas    = tk.Canvas(container, bg=GKN_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas, style="TFrame")

        # place the scrollable frame inside the canvas
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # update scrollregion when contents change
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        # allow mouse‐wheel scrolling
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        )

        # ─── BUILD YOUR WEIGHT / EARLIEST INPUT ROWS ─────────────────────────────
        # Now includes Latest Finish Time column
        # header row
        hdr = ttk.Frame(scrollable, style="TFrame")
        hdr.pack(fill="x", pady=(0,2))
        ttk.Label(hdr, text="Job ID",                width=20, anchor="w")\
            .grid(row=0, column=0, padx=5)
        ttk.Label(hdr, text="Weight",                width=10, anchor="w")\
            .grid(row=0, column=1, padx=5)
        ttk.Label(hdr, text="Earliest (HHMM)",       width=12, anchor="w")\
            .grid(row=0, column=2, padx=5)
        ttk.Label(hdr, text="Latest Finish (HHMM)",  width=15, anchor="w")\
            .grid(row=0, column=3, padx=5)
        ttk.Label(hdr, text="Precedence (comma-sep.)", width=20, anchor="w")\
            .grid(row=0, column=4, padx=5)


        self.params = {}
        for op in app.selected_ops:
            runs = app.max_runs.get(op, 1)
            for k in range(runs):
                frm = ttk.Frame(scrollable, style="TFrame")
                frm.pack(fill="x", pady=2)

                # Job ID label
                ttk.Label(frm, text=f"{op}_{k}", width=20, anchor="w").grid(row=0, column=0, padx=(0,5))
                # Weight entry
                ws = ttk.Entry(frm, width=10); ws.insert(0, '1')
                ws.grid(row=0, column=1, padx=5)
                # Earliest start entry
                es = ttk.Entry(frm, width=10); es.insert(0, '0700')
                es.grid(row=0, column=2, padx=5)
                # Latest finish entry
                lf = ttk.Entry(frm, width=15); lf.insert(0, '')
                lf.grid(row=0, column=3, padx=5)
                # Precedence entry
                pr = ttk.Entry(frm, width=20, foreground='gray')
                pr.insert(0, 'e.g. K01_0,K09_0')
                def _clear(e, entry=pr):
                    entry.delete(0,'end'); entry.config(foreground='black')
                pr.bind("<FocusIn>", _clear)
                pr.grid(row=0, column=4, padx=5)   
                # store tuple of four
                self.params[f"{op}_{k}"] = (ws, es, lf, pr)

        # finally, show this frame
        self.pack(fill="both", expand=True)

    def on_run(self):
        # gather user inputs
        weights, earliest, latest, precedence = {}, {}, {}, {}
        earliest['program_start'] = self.app.program_start_minutes

        for jid, (we, ee, lf, pr) in self.params.items():
            op = jid.rsplit('_', 1)[0]

            try:
                weights[op] = float(we.get())
            except ValueError:
                weights[op] = 1.0
            # earliest start
            try:
                hh, mm = int(ee.get()[:2]), int(ee.get()[2:])
                earliest[op] = hh * 60 + mm
            except:
                earliest[op] = self.app.program_start_minutes
            # latest finish
            try:
                h2, m2 = int(lf.get()[:2]), int(lf.get()[2:])
                latest[op] = h2 * 60 + m2
            except:
                latest[op] = None
             # precedence: parse comma-separated job IDs
            raw = pr.get().strip()
            if raw:                 # split on commas, strip whitespace
               precedence[jid] = [s.strip() for s in raw.split(',') if s.strip()]
            else:
                precedence[jid] = []

        # store back on the app
        self.app.weights          = weights
        self.app.earliest         = earliest
        self.app.latest_finishes  = latest
        self.app.precedence       = precedence
        # remove this frame next
        self.app.content.place_forget()
        self.destroy()

        # Create loading window
        loading = LoadingWindow(self.app, "Preparing to solve…")
        
        def solve_schedule():
            try:
                # If neither simulation nor Gantt, export & quit
                if not (self.app.show_simulation or self.app.show_gantt):
                    loading.update_message("Solving schedule and exporting...")
                    sched, tasks, ms = solve_throughput_with_earliest(
                        self.app.selected_ops,
                        self.app.sd,
                        self.app.ops,
                        weights,
                        self.app.max_runs,
                        self.app.horizon,
                        self.app.station_caps,
                        earliest,
                        latest,
                        precedence = self.app.precedence
                    )
                    helper = ScheduleFrame.__new__(ScheduleFrame)
                    helper.sched = sched
                    helper.tasks = tasks
                    helper.selected_ops = self.app.selected_ops
                    helper.ops = self.app.ops
                    helper.weights = weights
                    helper.max_runs = self.app.max_runs
                    helper.earliest = earliest
                    helper.base_minutes = self.app.program_start_minutes
                    helper.export_to_excel()
                    loading.destroy()
                    self.app.destroy()
                    return

                # Otherwise solve for GUI
                loading.update_message("Generating schedule...")
                sched, tasks, ms = solve_throughput_with_earliest(
                    self.app.selected_ops,
                    self.app.sd,
                    self.app.ops,
                    weights,
                    self.app.max_runs,
                    self.app.horizon,
                    self.app.station_caps,
                    earliest,
                    latest,
                    precedence=self.app.precedence
                )

                # check feasibility
                if not sched:
                    loading.destroy()
                    messagebox.showerror(
                        "Scheduling Error",
                        "Unable to meet latest-finish constraints. Please adjust your parameters."
                    )
                    # re-open run params
                    RunParamsFrame(self.master, self.app)
                    return

                # Update UI in main thread
                def create_schedule_frame():
                    self.app.content.place_forget()
                    self.destroy()
                    ScheduleFrame(
                        self.app,
                        sched, tasks, self.app.sd, ms,
                        self.app.selected_ops,
                        self.app.ops,
                        weights,
                        self.app.max_runs
                    )
                    loading.destroy()

                self.after(0, create_schedule_frame)

            except Exception as e:
                loading.destroy()
                messagebox.showerror("Error", str(e))
                RunParamsFrame(self.master, self.app)

        # Run solving in separate thread
        Thread(target=solve_schedule, daemon=True).start()