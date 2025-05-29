# scheduler/tasks.py

from .load_data import movement_time
from .utils import (station_xy,make_station_colors,minutes_to_hhmm,hhmm_to_minutes,axis_time_formatter,find_json,)
from Data.universal_variable import DEFAULT_HORIZON
__all__ = ["build_tasks", "build_tasks_with_storage"]

def build_tasks(seq, stations_dict):
    """
    Build a flat list of ("PROCESS"/"MOVE", station, duration, from_st, to_st, min_dur, max_dur)
    for a single operation sequence.  No storage buffers.
    """
    tasks = []
    # Initial PROCESS at S
    stn0, min0, max0 = seq[0]
    tasks.append(("PROCESS", "S", min0, None, None, min0, max0))
    # MOVE to the first real station
    next_st = seq[1][0]
    tasks.append(("MOVE", None, movement_time("S", next_st, stations_dict), "S", next_st, None, None))

    for i, (stn, mind, maxd) in enumerate(seq[1:], start=1):
        if mind > 0:
            tasks.append(("PROCESS", stn, mind, None, None, mind, maxd))
        nxt = seq[i+1][0] if i+1 < len(seq) else "FIN"
        tasks.append(("MOVE", None, movement_time(stn, nxt, stations_dict), stn, nxt, None, None))

    return tasks

def build_tasks_with_storage(seq, stations_dict):
    """
    Same as build_tasks but injects intermediate STORAGE steps
    using buffers S14, S15, S16 in round-robin.
    """
    tasks = []
    holding = ["S14", "S15", "S16"]

    for i, (stn, mind, maxd) in enumerate(seq):
        # PROCESS
        if mind > 0:
            tasks.append(("PROCESS", stn, mind, None, None, mind, maxd))

        # if not last, then MOVE→STORAGE→MOVE
        if i+1 < len(seq):
            next_st = seq[i+1][0]
            buf = holding[i % len(holding)]
            tasks.append(("MOVE", None, movement_time(stn, buf, stations_dict), stn, buf, None, None))
            tasks.append(("STORAGE", buf, 0, None, None, None, None))
            tasks.append(("MOVE", None, movement_time(buf, next_st, stations_dict), buf, next_st, None, None))

    return tasks
