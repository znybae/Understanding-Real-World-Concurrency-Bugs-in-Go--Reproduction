import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


CASES = [
    ("docker_24007_buggy", "Docker #24007 · buggy", "EXPECTED_PANIC", "Channel panic"),
    ("k8s_5316_buggy", "Kubernetes #5316 · buggy", "EXPECTED_BLOCKING", "Blocking timeout"),
    ("docker_25384_buggy", "Docker #25384 · buggy", "EXPECTED_BLOCKING", "WaitGroup timeout"),
    ("docker_25384_fixed", "Docker #25384 · fixed", "FIXED_PASS", "Test passed"),
    ("docker_27037_buggy", "Docker #27037 · buggy", "EXPECTED_RACE", "Race detected"),
    ("docker_27037_fixed", "Docker #27037 · fixed", "FIXED_PASS", "Test passed"),
]

parser = argparse.ArgumentParser()
parser.add_argument("summary", type=Path, help="Path to the run's summary.tsv")
args = parser.parse_args()

with args.summary.open(newline="", encoding="utf-8") as source:
    rows = list(csv.DictReader(source, delimiter="\t"))

fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
for position, (case, label, expected, outcome) in enumerate(CASES):
    runs = [row for row in rows if row["case"] == case]
    if not runs:
        parser.error(f"No experiment rows found for {case}")
    matches = sum(
        row["result"] == expected and row["checker_exit_code"] == "0"
        for row in runs
    )
    rate = 100 * matches / len(runs)
    color = "#247568" if expected == "FIXED_PASS" else "#345D91"
    ax.barh(position, rate, height=0.55, color=color)
    ax.text(rate + 2, position, f"{outcome} · {matches}/{len(runs)}", va="center", fontsize=9)

ax.set_yticks(range(len(CASES)), [case[1] for case in CASES])
ax.invert_yaxis()
ax.set_xlim(0, 145)
ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
ax.set_xlabel("Runs matching the expected outcome")
ax.set_title("Reproduction outcomes · Go 1.10.8", loc="left")
ax.set_axisbelow(True)
ax.grid(axis="x", alpha=0.2)
ax.spines[["top", "right", "left"]].set_visible(False)

output = Path(__file__).resolve().parents[1] / "report" / "figures" / "reproduction_outcomes.pdf"
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output)
print(f"Saved {output}")
