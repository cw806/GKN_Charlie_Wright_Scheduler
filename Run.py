import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from Scheduler.load_data import load_data
from Scheduler.model     import solve_throughput_with_earliest
from GUI.main_app        import MainApp
if __name__ == "__main__":
    # (MainApp already calls load_data() internally, so you might not even
    # need to import the solver here unless you’re wiring it up yourself.)
    app = MainApp()
    app.mainloop()