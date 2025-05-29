# animation.py
import tkinter as tk

class Animator:
    def __init__(self, parent, data):
        self.parent  = parent
        self.data    = data
        self.playing = False

    def start(self):
        self.play()

    def play(self):
        if not self.playing:
            self.playing = True
            self.tick()

    def pause(self):
        self.playing = False

    def seek(self, t):
        # Jump to specified time
        self.data.current_time = t
        self.update_components(t)

    def tick(self):
        if not self.playing:
            return
        # Increment time, respecting the makespan
        t = min(self.data.current_time + self.data.dt, self.data.makespan)
        self.data.current_time = t
        # Update slider if present
        if self.data.slider:
            self.data.slider.set(t)
        # Refresh both simulation and Gantt views
        self.update_components(t)
        # Schedule next tick
        if t < self.data.makespan:
            self.parent.after(int(self.data.delay), self.tick)

    def update_components(self, t):
        # Delegate to canvases
        self.parent.sim.update(t)
        self.parent.gantt.update(t)
