# scheduler/load_data.py
from .utils import (station_xy,make_station_colors,minutes_to_hhmm,hhmm_to_minutes,axis_time_formatter,find_json,)
from Data.universal_variable import TIME_UNIT, DEFAULT_HORIZON
import json
import os
import time
__all__ = ["load_data", "movement_time"]
# We’ll cache travel_times here after load_data is called
_travel_times = {}

def load_data(json_filename="operations_data.json"):
    # This module lives in …/Scheduler/load_data.py
    base = os.path.dirname(__file__)

    # first look for the file right next to this code
    candidate = os.path.join(base, json_filename)

    # if it’s not there, assume you meant the project-root/data/ folder
    if not os.path.isfile(candidate):
        candidate = os.path.abspath(os.path.join(base, "..", "data", json_filename))

    with open(candidate, 'r') as f:
        data = json.load(f)

    global travel_times
    travel_times = data.get("Travel_Times", {})

    return data["stations"], data["operations"]



def movement_time(stnA, stnB, stations_dict):
    """
    Return the cached travel time (in minutes) from stnA → stnB (default 1.0 if missing).
    """
    return _travel_times.get(stnA, {}).get(stnB, 1.0)
