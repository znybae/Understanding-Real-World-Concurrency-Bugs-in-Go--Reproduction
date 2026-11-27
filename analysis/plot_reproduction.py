import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


NAVY = "#244B6B"
TEAL = "#18838B"
GRID = "#DDE5EA"
TEXT = "#24323B"

CASES = [
    ("docker_24007_buggy", "Docker #24007 - buggy", "EXPECTED_PANIC", "panic"),
    ("k8s_5316_buggy", "Kubernetes #5316 - buggy", "EXPECTED_BLOCKING", "timeout"),
    ("docker_25384_buggy", "Docker #25384 - buggy", "EXPECTED_BLOCKING", "timeout"),
    ("docker_25384_fixed", "Docker #25384 - fixed", "FIXED_PASS", "pass"),
    ("docker_27037_buggy", "Docker #27037 - buggy", "EXPECTED_RACE", "race warning"),
    ("docker_27037_fixed", "Docker #27037 - fixed", "FIXED_PASS", "pass"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path, help="Path to the run's summary.tsv")
    args = parser.parse_args()

    with args.summary.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))

    plt.rcParams.update({
        "font.size": 9.5,
        "axes.titlesize": 13,
        "axes.labelcolor": TEXT,
        "text.color": TEXT,
        "xtick.color": "#5B6770",
        "ytick.color": TEXT,
        "pdf.fonttype": 42,
    })

    labels, rates, notes, colors = [], [], [], []
    for case, label, expected, outcome in CASES:
        runs = [row for row in rows if row["case"] == case]
        if not runs:
            parser.error(f"No experiment rows found for {case}")
        matches = sum(
            row["result"] == expected and row["checker_exit_code"] == "0"
            for row in runs
        )
        labels.append(label)
        rates.append(100 * matches / len(runs))
        notes.append(f"{matches}/{len(runs)}  {outcome}")
        colors.append(TEAL if expected == "FIXED_PASS" else NAVY)

    fig, ax = plt.subplots(figsize=(7.5, 4.25), layout="constrained")
    positions = range(len(labels))
    ax.barh(positions, rates, height=0.52, color=colors, edgecolor="white", linewidth=0.8)
    for position, note in zip(positions, notes):
        ax.text(102, position, note, va="center", fontsize=9, fontweight="semibold")

    ax.set_yticks(list(positions), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 120)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Runs matching the expected checker outcome")
    ax.set_title("All reproduced outcomes matched", loc="left", color=NAVY, fontweight="bold", pad=12)
    ax.text(0, 1.015, "Go 1.10.8 · three independent runs per case", transform=ax.transAxes,
            color="#5B6770", fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.tick_params(axis="y", length=0)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.legend(
        handles=[Patch(color=NAVY, label="Buggy variant"), Patch(color=TEAL, label="Fixed control")],
        loc="lower right", frameon=False, ncol=2, bbox_to_anchor=(1, -0.24),
    )

    output = Path(__file__).resolve().parents[1] / "report/figures/reproduction_outcomes.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
