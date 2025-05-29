# reliability_test2.py
import os, sys
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import csv
import time
from Scheduler.load_data import load_data
from Scheduler.model import solve_throughput_with_earliest
from tqdm import trange
from Data.universal_variable import TIME_UNIT
# 1) load your static data once
sd, ops = load_data()
station_caps = {st:1 for st in sd if st not in ('S','FIN')}

# 2) fix your test parameters here:
selected_ops = ['K01','K06','K15','K32']
weights      = {op: 1.0 for op in selected_ops}
max_runs     = {op: 20   for op in selected_ops}
horizon      = 22*60
earliest     = {'program_start': 0}

# 3) run N trials with a tqdm progress bar
results = []
start_time = time.time()
N = 1

for i in trange(1, N+1, desc="Reliability runs"):
    sched, all_tasks, _ = solve_throughput_with_earliest(
        selected_ops,
        sd,
        ops,
        weights,
        max_runs,
        horizon,
        station_caps,
        earliest,
        latest_finishes=None,
        time_unit=TIME_UNIT
    )

    # compute total runtime: first entry → last exit
    entries = [s for (jid, idx),(s,e) in sched.items()
                  if all_tasks[(jid,idx)]['type']=='PROCESS']
    exits   = [e for (jid, idx),(s,e) in sched.items()
                  if all_tasks[(jid,idx)]['type']=='PROCESS']
    if entries and exits:
        total_runtime = max(exits) - min(entries)
    else:
        total_runtime = 0

    throughput = len({jid for jid, idx in sched if idx == 0})
    results.append({
        'run':           i,
        'total_runtime': total_runtime,
        'throughput':    throughput,
    })

# 4) write out a CSV
with open('solver_reliability.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['run','total_runtime','throughput'])
    writer.writeheader()
    writer.writerows(results)

# 5) report wall-clock time
elapsed = time.time() - start_time
print(f"\nDone {N} runs in {elapsed:.1f}s ({elapsed/60:.2f}min).")
