# utils.py
import tkinter as tk
from matplotlib.ticker import FuncFormatter


def format_time_for_axis(base_minutes):
    """
    Returns a FuncFormatter for matplotlib axes, formatting x-values as HH:MM
    given a base_minutes offset.
    """
    def formatter(x, pos):
        total = base_minutes + x
        hh = int(total // 60) % 24
        mm = int(total % 60)
        return f"{hh:02d}:{mm:02d}"
    return FuncFormatter(formatter)


def make_scrollable(parent, **opts):
    """
    Creates a scrollable frame: returns (container, scrollable_frame).
    """
    cont = tk.Frame(parent)
    canvas = tk.Canvas(cont, **opts)
    scrollbar = tk.Scrollbar(cont, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    cont.rowconfigure(0, weight=1)
    cont.columnconfigure(0, weight=1)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.bind_all(
        "<MouseWheel>",
        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    )
    return cont, scroll_frame


def preprocess_schedule(sched, tasks, sd, makespan):
    """
    Build a Data object holding processed schedule info for the GUI.
    """
    class Data:
        pass
    data = Data()
    # Raw schedule components
    data.sched = sched
    data.tasks = tasks
    data.sd = sd
    data.makespan = makespan

    # Playback state
    data.current_time = 0.0
    data.dt = 0.5
    data.delay = 100

    # Screen dims and sim ratio
    data.width = tk._default_root.winfo_screenwidth()
    data.height = tk._default_root.winfo_screenheight()
    data.sim_ratio = 0.4

    # Styling and formatting
    from GUI.charts import make_station_colors, station_xy
    data.colors = make_station_colors(sd)
    data.formatter = format_time_for_axis(0)
    data.bar_height = 0.8
    data.bar_spacing = 1.0

    # Prepare intervals and sorted job list
    jobs = sorted({j for j,_ in sched})
    data.intervals = {}
    data.sorted_jobs = []
    for j in jobs:
        ivs = [(s, e, tasks[(jj, i)])
               for (jj, i), (s, e) in sched.items() if jj == j]
        ivs.sort(key=lambda x: x[0])
        data.intervals[j] = ivs
        data.sorted_jobs.append(j)

    # Station positioning & finish marker
    data.station_xy = lambda st: station_xy(
        st, sd, data.width, int(data.height * data.sim_ratio)
    )
    data.finish_point = data.station_xy('S')

    # Stubs to be wired by GUI
    def compute_position(jid, t):
        # replicate your old get_job_pos: find the (s,e) interval containing t
        ivs = sorted(
            ((i, (s,e)) for (j,i),(s,e) in data.sched.items() if j==jid),
            key=lambda x: x[1][0]
        )
        for idx, (s,e) in ivs:
            if s <= t < e:
                info = data.tasks[(jid, idx)]
                if info['type'] in ('PROCESS','STORAGE'):
                    x,y = data.station_xy(info.get('station') or 'S')
                    return (x, y, data.colors.get(info.get('station') or 'S'))
                # else it’s a MOVE: interpolate between stations
                a,b = info['from_st'], info['to_st']
                x1,y1 = data.station_xy(a)
                x2,y2 = data.station_xy(b)
                frac = (t-s)/(e-s) if e>s else 1
                return (x1 + frac*(x2-x1), y1 + frac*(y2-y1),
                        data.colors.get(b, 'black'))
        # if past all tasks, return finish point
        xf,yf = data.finish_point
        return (xf, yf, 'black')
    data.compute_position = compute_position
    data.update_clock_label = lambda t: None
    data.slider = None

    # GUI will attach these before running
    data.selected_ops = []
    data.ops = {}
    data.weights = {}
    data.max_runs = {}
    data.base_minutes = 0

    return data