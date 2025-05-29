# GUI/frames/schedule_frame/gantt_canvas.py
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GanttCanvas(ttk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data

        # bump bar_height so bars render thicker (~0.8 cm)
        self.bar_height = data.bar_height * 2.5
        spacing = self.bar_height * 0.5

        # ——— build scrollable container ———
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        vscroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)

        inner = ttk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor="nw")

        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def on_inner_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_inner_config)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        )

        # ——— build the Matplotlib figure ———
        self.fig = Figure(figsize=(data.width/100, data.height/100), dpi=100)
        self.ax  = self.fig.add_subplot(111)
        self.ax.xaxis.set_major_formatter(data.formatter)
        self.timeline = self.ax.axvline(0, color="red", linewidth=2)

        # draw all the bars
        self._draw_bars(spacing)

        # embed figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=inner)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.pack(fill="both", expand=True)

    def _draw_bars(self, spacing):
        # jobs in chronological order (earliest start at top)
        # compute each job's first process start
        def start_time(jid):
            ivs = [(s,e,info) for (s,e,info) in [(s,e,info) for (s,e,info) in self.data.intervals[jid]] if info['type']=='PROCESS']
            return min((s for s,e,info in ivs), default=0)
        jobs = sorted(self.data.sorted_jobs, key=lambda j: start_time(j))
        self.y_map = {jid: idx*(self.bar_height+spacing) for idx,jid in enumerate(jobs)}

        for jid in jobs:
            y = self.y_map[jid]
            ivs = self.data.intervals[jid]
            for s,e,info in ivs:
                dur = e - s
                color = (
                    "#777777" if info["type"] == "MOVE"
                    else self.data.colors.get(info.get("station","S"), "#CCCCCC")
                )
                self.ax.broken_barh(
                    [(s, dur)],
                    (y, self.bar_height),
                    facecolors=color,
                    edgecolors="black",
                    picker=True
                )

        max_y = max(self.y_map.values()) + self.bar_height
        self.ax.set_ylim(-spacing, max_y + spacing)
        self.ax.set_xlim(0, self.data.makespan)
        self.ax.set_xlabel("Time (min)")
        self.ax.set_yticks([self.y_map[j] + self.bar_height/2 for j in jobs])
        self.ax.set_yticklabels(jobs, fontsize=8)

    def update(self, t):
        self.timeline.set_xdata([t, t])
        self.canvas.draw_idle()
