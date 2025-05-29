import os, sys
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import time
import csv
import pandas as pd
from tkinter import filedialog
import tkinter as tk
from Data.universal_variable import TIME_UNIT, DEFAULT_HORIZON
from Scheduler.load_data import load_data
from Scheduler.model import solve_throughput_with_earliest

def select_input_file():
    """Open file dialog to select input file."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select Input File",
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
    )
    return file_path if file_path else "read_data.csv"

def run_historical(input_path: str = None,
                  output_csv: str = "historical_throughput.csv"):
    """
    Process historical data and generate throughput statistics.
    
    Args:
        input_path: Path to input file (Excel/CSV) with columns [Date, Sequence label]
        output_csv: Path to output CSV file for results
    """
    try:
        # Get input file if not specified
        if input_path is None:
            input_path = select_input_file()
        
        print(f"Reading data from: {os.path.abspath(input_path)}")
        
        # Read input data based on file extension
        if input_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_path, parse_dates=["Date"], dtype={"Sequence label": str})
        else:
            df = pd.read_csv(input_path, parse_dates=["Date"], dtype={"Sequence label": str})
        
        df["Date"] = df["Date"].dt.date

        # Load static scheduling data
        sd, ops = load_data()
        station_caps = {st:1 for st in sd if st not in ("S","FIN")}
        horizon = DEFAULT_HORIZON
        earliest = {"program_start": 0}

        # Get unique dates and operations
        all_dates = sorted(df["Date"].unique())
        all_ops = sorted(df["Sequence label"].unique())
        
        # Initialize results storage
        results = []
        t0 = time.time()

        # Process each date
        for day in all_dates:
            print(f"→ Processing {day}")
            
            # Get operations for this day
            sub = df[df["Date"] == day]
            counts = sub["Sequence label"].value_counts().to_dict()
            
            # Setup scheduling parameters
            selected_ops = list(counts)
            weights = {op:1.0 for op in selected_ops}
            max_runs = counts.copy()

            # Generate schedule
            sched, all_tasks, _ = solve_throughput_with_earliest(
                selected_ops, sd, ops, weights, max_runs,
                horizon, station_caps, earliest, 
                latest_finishes=None, time_unit=TIME_UNIT
            )

            if not sched:
                print(f"  ⚠️  Failed to generate schedule for {day}, skipping")
                continue

            # Calculate metrics
            procs = [(s,e) for (jid,idx),(s,e) in sched.items() 
                    if all_tasks[(jid,idx)]["type"]=="PROCESS"]
            
            if procs:
                starts, ends = zip(*procs)
                total_runtime = max(ends) - min(starts)
            else:
                total_runtime = 0.0
                
            throughput = sum(1 for (jid,idx) in sched if idx==0)

            # Store results for this day
            row = {
                "Date": day,
                "total_runtime": total_runtime,
                "throughput": throughput,
                **{op: counts.get(op, 0) for op in all_ops}
            }
            results.append(row)

        # Write output CSV
        fieldnames = ["Date", "total_runtime", "throughput"] + all_ops
        out_path = os.path.abspath(output_csv)
        
        with open(out_path, "w", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\nProcessed {len(results)} days in {time.time()-t0:.1f}s")
        print(f"Results written to: {out_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else "historical_throughput.csv"
    
    run_historical(input_file, output_file)