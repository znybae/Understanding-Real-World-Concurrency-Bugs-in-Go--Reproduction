#!/usr/bin/env python3
"""Summarize observed checks; never substitute for the paper's dataset metrics."""
import csv
import statistics
import sys
from pathlib import Path

def main():
    path = Path(sys.argv[1])
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    expected = {
        "docker_24007_buggy": "EXPECTED_PANIC",
        "k8s_5316_buggy": "EXPECTED_BLOCKING",
        "docker_25384_buggy": "EXPECTED_BLOCKING",
        "docker_25384_fixed": "FIXED_PASS",
        "docker_27037_buggy": "EXPECTED_RACE",
        "docker_27037_fixed": "FIXED_PASS",
    }
    output = path.with_name("statistics.csv")
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case", "runs", "expected_observations", "indicator_mean",
                         "indicator_sample_std", "at_least_three_runs"])
        for case, verdict in expected.items():
            selected = [r for r in rows if r["case"] == case]
            if not selected:
                raise ValueError("Missing case: " + case)
            values = [int(r["checker_exit_code"] == "0" and r["result"] == verdict)
                      for r in selected]
            writer.writerow([case, len(values), sum(values), statistics.mean(values),
                             statistics.stdev(values) if len(values) > 1 else "NA",
                             len(values) >= 3])
    print("Statistics:", output)
    print("Mean/std describe binary expected-outcome indicators, not runtime or the paper's aggregate detection rate.")

if __name__ == "__main__":
    main()