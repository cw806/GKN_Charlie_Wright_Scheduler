# initial_frame.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from Data.universal_variable import DEFAULT_HORIZON as default_horizon
import pandas as pd
from GUI.colours import GKN_TEXT, GKN_SECONDARY
import os
from Scheduler.model import solve_throughput_with_earliest
from GUI.frames.Loading_frame import LoadingWindow
from threading import Thread
import uuid
import json

class InitialFrame(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, style="TFrame")
        self.app = app

        # Header with centered title
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", pady=(10,5))
        title = ttk.Label(
            header,
            text="Scheduler Options",
            font=("Segoe UI", 14, "bold"),
            foreground=GKN_SECONDARY
        )
        title.pack(pady=10)

        # Start time input
        input_frame = ttk.Frame(self, style="TFrame")
        input_frame.pack(fill="x", pady=5, padx=10)
        ttk.Label(input_frame, text="Start (HHMM):", foreground=GKN_TEXT).pack(side="left")
        self.start_entry = ttk.Entry(input_frame, width=6)
        # default display from app
        self.start_entry.insert(
            0,
            f"{self.app.program_start_minutes//60:02d}{self.app.program_start_minutes%60:02d}"
        )
        self.start_entry.pack(side="left", padx=(5,20))

        # Horizon field
        ttk.Label(input_frame, text="Horizon (min):", foreground=GKN_TEXT).pack(side="left")
        self.horizon_entry = ttk.Entry(input_frame, width=6)
        self.horizon_entry.insert(0, str(getattr(self.app, 'horizon', default_horizon)))
        self.horizon_entry.pack(side="left", padx=(5,20))

        # View options
        self.var_sim = tk.BooleanVar(value=self.app.show_simulation)
        self.var_gantt = tk.BooleanVar(value=self.app.show_gantt)
        opts_frame = ttk.Frame(self, style="TFrame")
        opts_frame.pack(fill="x", pady=5, padx=10)
        ttk.Checkbutton(opts_frame, text="Show Simulation", variable=self.var_sim).pack(side="left", padx=(0,10))
        ttk.Checkbutton(opts_frame, text="Show Gantt", variable=self.var_gantt).pack(side="left")

        # Operation selector
        ttk.Label(
            self,
            text="Select Operations & Max Runs",
            font=("Segoe UI", 12, "bold"),
            foreground=GKN_TEXT
        ).pack(pady=(15,5))
        self.lb = tk.Listbox(
            self,
            selectmode='multiple',
            exportselection=False,
            height=10,
            bg="white",
            fg=GKN_TEXT
        )
        for op in sorted(app.ops):
            self.lb.insert('end', op)
        self.lb.pack(fill='both', expand=True, padx=10)

        # Buttons frame
        btn_frame = ttk.Frame(self, style="TFrame")
        btn_frame.pack(pady=10, anchor="center")
        ttk.Button(btn_frame, text="Import History…", command=self.on_import_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Run ▶", command=self.on_run, style="TButton").pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel, style="TButton").pack(side="left")
        self.pack(fill="both", expand=True)
        ttk.Button(btn_frame,text="Import FlightBar JSON", command=self.on_import_flightbar_json).pack(side="left", padx=5)
    def on_import_flightbar_json(self):
        """Load a FlightBar JSON, extract kNumbers→ops and efficiencies→weights,
        and then either export Excel or show the schedule GUI."""
        path = filedialog.askopenfilename(
            title="Select FlightBar JSON",
            filetypes=[("JSON files","*.json")]
        )
        if not path:
            return

        # 1) load JSON
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("JSON load error", f"Could not read {path}:\n{e}")
            return

        # 2) extract ops, weights, counts
        counts = {}
        weights = {}
        for fb in data.get("flightBars", []):
            k = fb.get("kNumber")
            if k not in self.app.ops:
                continue
            eff = fb.get("efficiency", 1.0)
            if not k:
                continue
            counts[k] = counts.get(k, 0) + 1
            # if multiple bars of same k, just keep the last efficiency
            weights[k] = eff

        if not counts:
            messagebox.showinfo("No flightBars", "No valid flightBars found in that file.")
            return

        # store on app
        self.app.selected_ops = list(counts.keys())
        self.app.max_runs     = counts
        self.app.weights      = weights

        # earliest = program start for all
        self.app.earliest = {"program_start": 0,
                            **{k: 0 for k in counts}}

        # 3) call the solver immediately
        from .schedule_frame.frame import ScheduleFrame

        loading = LoadingWindow(self.app, "Solving flight-bar schedule…")

        def worker():
            try:
                # run the solver
                sched, tasks, makespan = solve_throughput_with_earliest(
                    self.app.selected_ops,
                    self.app.sd,
                    self.app.ops,
                    self.app.weights,
                    self.app.max_runs,
                    getattr(self.app, 'horizon', default_horizon),
                    self.app.station_caps,
                    self.app.earliest
                )

                # done solving, now dispatch back to UI thread
                def finish():
                    loading.destroy()

                    # if neither view requested, export & quit
                    if not (self.app.show_simulation or self.app.show_gantt):
                        helper = ScheduleFrame.__new__(ScheduleFrame)
                        helper.sched        = sched
                        helper.tasks        = tasks
                        helper.selected_ops = self.app.selected_ops
                        helper.ops          = self.app.ops
                        helper.weights      = self.app.weights
                        helper.max_runs     = self.app.max_runs
                        helper.earliest     = self.app.earliest
                        helper.base_minutes = 0
                        helper.export_to_excel()
                        self.app.destroy()
                    else:
                        # go straight to the full GUI
                        self.destroy()
                        ScheduleFrame(
                            self.app,
                            sched, tasks, self.app.sd, makespan,
                            self.app.selected_ops,
                            self.app.ops,
                            self.app.weights,
                            self.app.max_runs
                        )

                self.app.after(0, finish)

            except Exception as ex:
                # on error, hide loading and show message
                def show_err():
                    loading.destroy()
                    messagebox.showerror("Error", str(ex))
                self.app.after(0, show_err)

        # fire off the solver thread
        Thread(target=worker, daemon=True).start()

    def on_import_history(self):

        """Load historical Excel, compute per-day schedules, export reports."""
        path = filedialog.askopenfilename(
            title="Select history Excel",
            filetypes=[("Excel files","*.xlsx;*.xls")]
        )
        if not path:
            return

        # try loading
        try:
            df = pd.read_excel(path, parse_dates=["Date"], dtype={"Sequence label": str})
            df["Date"] = df["Date"].dt.date
        except Exception as e:
            messagebox.showerror("Load error", f"Could not read {path}:\n{e}")
            return

        # fire off a background thread to do all the work:
        loading = LoadingWindow(self.app, "Preparing historical run…")

        def worker():
            try:
                # results containers
                summary_rows = []
                detail_rows  = []

                # static data
                sd, ops = self.app.sd, self.app.ops
                station_caps = self.app.station_caps
                horizon      = default_horizon
                earliest     = {"program_start": 0}

                all_dates = sorted(df["Date"].unique())

                for idx, day in enumerate(all_dates, start=1):
                    loading.update_message(f"Scheduling {day} ({idx}/{len(all_dates)})…")
                    sub = df[df["Date"] == day]
                    counts = sub["Sequence label"].value_counts().to_dict()
                    if not counts:
                        continue

                    # run the solver
                    sched, tasks, _ = solve_throughput_with_earliest(
                        selected_ops    = list(counts),
                        stations_dict   = sd,
                        operations_dict = ops,
                        weights         = {op:1.0 for op in counts},
                        max_runs        = counts,
                        horizon         = horizon,
                        station_caps    = station_caps,
                        earliest_starts = {'program_start': 0, **{op:0 for op in counts}}
                    )

                    # build summary: one row per product
                    for op, cnt in counts.items():
                        for k in range(cnt):
                            jid = f"{op}_{k}"
                            starts = [s for (j,i),(s,e) in sched.items()
                                      if j==jid and tasks[(j,i)]["type"]=="PROCESS"]
                            ends   = [e for (j,i),(s,e) in sched.items()
                                      if j==jid and tasks[(j,i)]["type"]=="PROCESS"]
                            if not starts: continue
                            ent = min(starts); ext = max(ends)
                            hhmm = lambda m: f"{int(m//60):02d}:{int(m%60):02d}"
                            summary_rows.append({
                                "Date": day,
                                "Product": op,
                                "Run": k,
                                "Entry (clock)": hhmm(ent),
                                "Exit (clock)":  hhmm(ext),
                                "Timespan (min)": ext - ent
                            })

                    # build details: one row per PROCESS task
                    for (jid, idx2), (s,e) in sched.items():
                        info = tasks[(jid, idx2)]
                        if info["type"]!="PROCESS": continue
                        hhmm = lambda m: f"{int(m//60):02d}:{int(m%60):02d}"
                        detail_rows.append({
                            "Date": day,
                            "Job ID": jid,
                            "Entry (clock)": hhmm(s),
                            "Exit (clock)":  hhmm(e),
                            "Duration": round(e - s,1)
                        })

                # once done, write out Excel files
                loading.update_message("Writing summary Excel…")
                sum_df = pd.DataFrame(summary_rows)
                sum_file = self._unique_filename("history_summary", ".xlsx")
                sum_df.to_excel(sum_file, index=False)

                loading.update_message("Writing detail Excel…")
                det_df = pd.DataFrame(detail_rows)
                det_file = self._unique_filename("history_details", ".xlsx")
                det_df.to_excel(det_file, index=False)

                # back on UI thread: close loader, inform user, open files
                def on_finish():
                    loading.destroy()
                    messagebox.showinfo("Done",
                        f"Summary → {sum_file}\nDetails → {det_file}")
                    os.startfile(sum_file)
                    os.startfile(det_file)
                self.app.after(0, on_finish)

            except Exception as error:
                def on_error(error=error):
                    loading.destroy()
                    messagebox.showerror("Error", str(error))
                self.app.after(0, on_error)

        Thread(target=worker, daemon=True).start()
    def _unique_filename(self, base, ext):
        idx = 0
        while True:
            fn = f"{base}{'' if idx==0 else f'_{idx}'}{ext}"
            if not os.path.exists(fn):
                return fn
            idx += 1
    def on_run(self):
        # Validate operations
        sel = [self.lb.get(i) for i in self.lb.curselection()]
        if not sel:
            messagebox.showwarning("No operations", "Please select at least one operation.")
            return
        # Store selected ops on app
        self.app.selected_ops = sel

        # Parse and store start time

        # Validate operations
        sel = [self.lb.get(i) for i in self.lb.curselection()]
        if not sel:
            messagebox.showwarning("No operations", "Please select at least one operation.")
            return

        # Parse and store start time
        try:
            val = self.start_entry.get()
            hh, mm = int(val[:2]), int(val[2:])
            self.app.program_start_minutes = hh * 60 + mm
        except:
            messagebox.showwarning("Invalid time", "Please enter start time as HHMM.")
            return

        # Parse and store horizon
        try:
            self.app.horizon = int(self.horizon_entry.get())
        except ValueError:
            self.app.horizon = default_horizon

        # Store view flags
        self.app.show_simulation = self.var_sim.get()
        self.app.show_gantt = self.var_gantt.get()

        # Proceed
        self.destroy()
        from .max_runs_frame import MaxRunsFrame
        MaxRunsFrame(self.master, self.app)

    def on_cancel(self):
        self.app.destroy()
