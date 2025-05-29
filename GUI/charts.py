# charts.py
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex

def station_xy(stn, sd, w, h):
    """
    Compute on-canvas x,y coordinates based on station metadata in sd.

    Args:
        stn (str): Station identifier.
        sd (dict): Station dictionary containing 'x' and 'row' positions.
        w (int): Canvas width in pixels.
        h (int): Canvas height in pixels.

    Returns:
        tuple: (x, y) pixel coordinates for the station.
    """
    # margin from edges
    m = 80
    aw, ah = w - 2*m, h - 2*m
    row_sp = ah / max(1, max(v.get('row', 0) for v in sd.values()))

    # scale x by max x index
    maxx = max((v.get('x', 0) for v in sd.values()), default=1)
    sx = aw / max(1, maxx)

    # default location for unknown station
    if stn not in sd:
        return m, h - m

    x = m + sd[stn]['x'] * sx
    y = h - m - sd[stn]['row'] * row_sp
    return x, y

def make_station_colors(sd):
    """
    Assign each station a unique color from the Tab20 colormap.

    Args:
        sd (dict): Station dictionary; keys are station IDs.

    Returns:
        dict: Mapping station ID -> hex color string.
    """
    keys = sorted(sd.keys(), key=lambda s: (sd[s].get('row', 0), sd[s].get('x', 0)))
    cmap = plt.get_cmap('tab20')
    return {k: to_hex(cmap(i % 20)) for i, k in enumerate(keys)}
