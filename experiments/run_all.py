"""Run every experiment in order and report how long each took."""

from __future__ import annotations

import importlib
import time

from _common import banner, provenance, save

ORDER = ("e1_main", "e2_ablation", "e3_costs", "e4_transfer", "e5_shield",
         "e6_worked_example", "e6_premature", "e7_escalation")


def main() -> None:
    timings = {}
    for name in ORDER:
        start = time.time()
        importlib.import_module(name).main()
        timings[name] = round(time.time() - start, 2)
    banner("all experiments complete")
    for name, seconds in timings.items():
        print(f"  {name:20s} {seconds:8.2f}s")
    save("run_all", {"provenance": provenance(experiment="run_all"),
                     "timings_seconds": timings})


if __name__ == "__main__":
    main()
