# scheduler/utils.py

import os
import math
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ----------------------------------------------------------------------------
# -- Constants
# ----------------------------------------------------------------------------

# Relative path to your operations JSON (you can override this in load_data)
OPERATIONS_JSON = os.path.join(os.path.dirname(__file__), "operations_range.json")


# ----------------------------------------------------------------------------
# -- Coordinate & Colour Utilities
# ----------------------------------------------------------------------------

def station_xy(stn, sd, width, height, margin=80):
    """
    Map station ID to an (x, y) pixel position.
    - sd: station‐dictionary loaded from JSON, must contain 'x' and 'row' keys.
    - width, height: size of your drawing canvas.
    - margin: pixel margin around the edges.
    """
    aw, ah = width - 2*margin, height - 2*margin
    row_sp = ah / 2
    maxx = max(v['x'] for v in sd.values()) or 1
    scale_x = aw / maxx

    if stn not in sd:
        # fallback: bottom‐left
        return margin, height - margin

    x = margin + sd[stn]['x'] * scale_x
    y = height - margin - sd[stn]['row'] * row_sp
    return x, y


def make_station_colors(sd, cmap_name="tab20"):
    """
    Assign each station in sd a unique hex colour, based on matplotlib's tab20.
    """
    keys = sorted(sd.keys(), key=lambda s:(sd[s]['row'], sd[s]['x']))
    cmap = plt.get_cmap(cmap_name)
    return {k: to_hex(cmap(i % cmap.N)) for i,k in enumerate(keys)}


# ----------------------------------------------------------------------------
# -- Time‐Formatting Utilities
# ----------------------------------------------------------------------------

def minutes_to_hhmm(m):
    """
    Convert an integer minute‐count into an HH:MM string (24h clock).
    """
    h = int(m) // 60
    mm = int(m) % 60
    return f"{h:02d}:{mm:02d}"


def hhmm_to_minutes(s):
    """
    Parse a string like “0730” or “07:30” into total minutes since 00:00.
    """
    s = s.strip()
    if ":" in s:
        parts = s.split(":")
    else:
        parts = [s[:2], s[2:]]
    h, mm = map(int, parts)
    return h*60 + mm


def axis_time_formatter(program_start_min):
    """
    Return a matplotlib.FuncFormatter that will display the x‐axis
    in HH:MM, offset by program_start_min.
    """
    def fmt(x, pos):
        # x is minutes since program_start
        absolute = program_start_min + x
        return minutes_to_hhmm(absolute)
    return FuncFormatter(fmt)


# ----------------------------------------------------------------------------
# -- File & Path Utilities
# ----------------------------------------------------------------------------

def find_json(name):
    """
    Look in the package directory for a JSON file.
    """
    here = os.path.dirname(__file__)
    path = os.path.join(here, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not locate {name} under {here}")
    return path
