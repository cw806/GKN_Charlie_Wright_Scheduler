# sim_canvas.py
import tkinter as tk

class SimulationCanvas(tk.Canvas):
    """
    Canvas for animating job movements through stations.
    """
    def __init__(self, parent, data):
        height = int(parent.winfo_screenheight() * data.sim_ratio)
        super().__init__(parent, bg="white", width=data.width, height=height)
        self.data = data
        # Draw station outlines
        self.draw_stations()
        # Initialize job ovals and labels
        self._init_jobs()
        # Pack at top above Gantt
        self.pack(side="top", fill="both", expand=False)

    def draw_stations(self):
        """
        Draw fixed station rectangles and labels on the canvas.
        """
        for st in self.data.sd:
            x, y = self.data.station_xy(st)
            c    = self.data.colors[st]
            self.create_rectangle(x-30, y-30, x+30, y+30, fill=c, outline="black")
            self.create_text(x, y-40, text=st, font=("Arial",12,"bold"))
        # Record finish position
        self.finished = self.data.finish_point

    def _init_jobs(self):
        """
        Pre-create ovals and text for each job, hidden initially.
        """
        self.data.job_items = {}
        for jid in self.data.sorted_jobs:
            oval = self.create_oval(0,0,30,30, fill="black", outline="white", width=2)
            lbl  = self.create_text(0,0, text=jid, font=("Arial",10,"bold"), fill="white")
            self.data.job_items[jid] = (oval, lbl)

    def update(self, t):
        """
        Move each job oval/text to its position at time t.
        """
        for jid, (oval, lbl) in self.data.job_items.items():
            pos = self.data.compute_position(jid, t)
            if pos is None:
                # Hide before job starts or after finish
                self.itemconfig(oval, state='hidden')
                self.itemconfig(lbl, state='hidden')
            else:
                x, y, color = pos
                # Show and move
                self.itemconfig(oval, state='normal', fill=color)
                self.coords(oval, x-15, y-15, x+15, y+15)
                self.coords(lbl, x, y)
        # Optionally update a clock label if bound
        if hasattr(self.data, 'update_clock_label'):
            self.data.update_clock_label(t)