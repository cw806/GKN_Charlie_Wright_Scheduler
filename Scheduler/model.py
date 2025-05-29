import multiprocessing
from functools import lru_cache
from pathlib import Path
import json
import math
from ortools.sat.python import cp_model
from .tasks import build_tasks
from .load_data import movement_time
from Data.universal_variable import TIME_UNIT, DEFAULT_HORIZON
from .utils import (
    station_xy,
    make_station_colors,
    minutes_to_hhmm,
    hhmm_to_minutes,
    axis_time_formatter,
    find_json,
)

__all__ = ["solve_throughput_with_earliest", "TIME_UNIT"]

# Expose module‐level default time unit so external scripts can import it
TIME_UNIT = TIME_UNIT  # ticks per minute as defined in universal_variable

def solve_throughput_with_earliest(
    selected_ops,
    stations_dict,
    operations_dict,
    weights,
    max_runs,
    horizon,
    station_caps,
    earliest_starts=None,
    latest_finishes=None,
    time_unit: int = TIME_UNIT,
    precedence:   dict  = None,            # ← new!


):
    """
    CP-SAT schedule with optional earliest-start and latest-finish constraints per operation.
    Returns (sched, all_tasks_dict, horizon).
    - sched[(job_id, idx)] = (start_min, end_min)
    - all_tasks_dict[(job_id, idx)] = metadata dict with 'start','end','interval',...
    """
    # convert horizon minutes → ticks
    H_t = int(round(horizon * time_unit))
    model = cp_model.CpModel()
    # Create a hash of the problem parameters
    problem_hash = str(hash((
        tuple(selected_ops),
        tuple(sorted(weights.items())),
        tuple(sorted(max_runs.items())),
        horizon,
        tuple(sorted(station_caps.items())),
        tuple(sorted((earliest_starts or {}).items())),
        tuple(sorted((latest_finishes or {}).items()))
    )))

    # adjust earliest-start values relative to program start
    program_start = (earliest_starts or {}).get("program_start", 0)
    earliest_t = {
        op: max(0, int((t - program_start) * time_unit))
        for op, t in (earliest_starts or {}).items()
        if op != "program_start" and t is not None
    }
    # adjust latest-finish values relative to program start
    latest_t = {
        op: max(0, int((t - program_start) * time_unit))
        for op, t in (latest_finishes or {}).items()
        if op != "program_start" and t is not None
    }

    # build templates & run counts
    templates, run_counts = {}, {}
    for op in selected_ops:
        seq = operations_dict[op]
        tpl = build_tasks(seq, stations_dict)
        templates[op] = tpl
        if max_runs.get(op, 0) > 0:
            run_counts[op] = max_runs[op]
        else:
            minimal = sum(entry[2] for entry in tpl)
            run_counts[op] = int(horizon // minimal) + 1

    all_tasks, job_presence = {}, {}
    station_intervals, move_D, move_S = {}, [], []

    # create variables and intervals
    for op in selected_ops:
        w = weights.get(op, 1)
        force_presence = (op in latest_t)
        tpl = templates[op]
        for k in range(run_counts[op]):
            jid = f"{op}_{k}"
            p = model.NewBoolVar(f"pres_{jid}")
            job_presence[jid] = (p, w)
            if force_presence:
                model.Add(p == 1)
            for idx, entry in enumerate(tpl):
                tt, stn, dur_min, fr, to, *_ = entry
                dur_t = int(math.ceil(dur_min * time_unit))
                name = f"{jid}_t{idx}_{tt}"
                s = model.NewIntVar(0, H_t - dur_t, f"{name}_s")
                e = model.NewIntVar(0, H_t,        f"{name}_e")
                iv = model.NewOptionalIntervalVar(s, dur_t, e, p, f"{name}_iv")

                # earliest-start on the first interval
                if idx == 0 and op in earliest_t:
                    model.Add(s >= earliest_t[op]).OnlyEnforceIf(p)
                # latest-finish on the last interval
                if idx == len(tpl) - 1 and op in latest_t:
                    model.Add(e <= latest_t[op]).OnlyEnforceIf(p)

                all_tasks[(jid, idx)] = {
                    "type":     tt,
                    "station":  stn,
                    "from_st":  fr,
                    "to_st":    to,
                    "start":    s,
                    "end":      e,
                    "interval": iv,
                    "pres":     p,
                }
                # collect for capacity
                if tt == "PROCESS" and stn not in ("S", "FIN"):
                    station_intervals.setdefault(stn, []).append(iv)
                if tt == "MOVE" and to not in ("S", "FIN"):
                    station_intervals.setdefault(to, []).append(iv)
                if tt == "MOVE" and fr and fr.startswith("D"):
                    move_D.append(iv)
                if tt == "MOVE" and fr and fr.startswith("S"):
                    move_S.append(iv)

    # chain precedence
    for op in selected_ops:
        for k in range(run_counts[op]):
            jid = f"{op}_{k}"
            p, _ = job_presence[jid]
            for idx in range(len(templates[op]) - 1):
                curr = all_tasks[(jid, idx)]
                nxt  = all_tasks[(jid, idx + 1)]
                model.Add(nxt["start"] == curr["end"]).OnlyEnforceIf(p)
    # ─── USER-DEFINED PRECEDENCE ────────────────────────────────────────────
    # precedence: { "K01_0": ["K09_0","K15_1"], ... }
    for jid, preds in (precedence or {}).items():
        # make sure this job actually got created
        idxs = [i for (j,i) in all_tasks if j == jid]
        if not idxs:
            continue
        first_idx = min(idxs)
        s_jid = all_tasks[(jid, first_idx)]["start"]
        p_jid = all_tasks[(jid, first_idx)]["pres"]
        for before_jid in preds:
            # skip any before_jid that isn't scheduled
            before_idxs = [i for (j,i) in all_tasks if j == before_jid]
            if not before_idxs:
                continue
            last_idx = max(before_idxs)
            e_before = all_tasks[(before_jid, last_idx)]["end"]
            model.Add(s_jid >= e_before).OnlyEnforceIf(p_jid)
    # station capacities
    for stn, ivs in station_intervals.items():
        cap = station_caps.get(stn, 1)
        if cap == 1:
            model.AddNoOverlap(ivs)
        else:
            model.AddCumulative(ivs, [1] * len(ivs), cap)
    # move-line capacities
    if move_D:
        model.AddNoOverlap(move_D)
    if move_S:
        model.AddCumulative(move_S, [1] * len(move_S), 2)

    # finish-time vars
    finish_vars = []
    for jid, (p, _) in job_presence.items():
        lf = model.NewIntVar(0, H_t, f"fin_{jid}")
        for (j2, idx), info in all_tasks.items():
            if j2 == jid:
                model.Add(lf >= info["end"]).OnlyEnforceIf(p)
        finish_vars.append(lf)

    # objective: max throughput * BIGF – sum(finishes)
    BIGF = H_t * (sum(run_counts.values()) + 1)
    throughput = sum(p * w for p, w in job_presence.values())
    total_finish = sum(finish_vars)
    model.Maximize(throughput * BIGF - total_finish)
    # Solve with adaptive timeout
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = multiprocessing.cpu_count()
    
    st = solver.Solve(model)
    
    # If solution is optimal, cache it
    if st == cp_model.OPTIMAL:
        sched = {}
        for (jid, idx), info in all_tasks.items():
            if solver.Value(info["pres"]):
                sched[(jid, idx)] = (
                    solver.Value(info["start"]) / time_unit,
                    solver.Value(info["end"]) / time_unit,
                )
        solution = {
            'sched': sched,
            'all_tasks': all_tasks,
            'horizon': horizon
        }
        return sched, all_tasks, horizon
    
    if st == cp_model.FEASIBLE:
        # Found a feasible but not optimal solution
        sched = {}
        for (jid, idx), info in all_tasks.items():
            if solver.Value(info["pres"]):
                sched[(jid, idx)] = (
                    solver.Value(info["start"]) / time_unit,
                    solver.Value(info["end"]) / time_unit,
                )
        return sched, all_tasks, horizon
    elif st == cp_model.INFEASIBLE:
        # No feasible solution found
        print("No feasible solution found.")
    return {}, all_tasks, 0