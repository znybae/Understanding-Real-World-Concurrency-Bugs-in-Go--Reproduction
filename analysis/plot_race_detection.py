import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


NAVY = "#244B6B"
TEAL = "#18838B"
PALE = "#E4EBEF"
TEXT = "#24323B"


def load_team_counts(path):
    counts_file = path if path.is_file() else path / "race_warning_counts.tsv"
    if not counts_file.exists():
        raise FileNotFoundError(f"Missing race-warning count file: {counts_file}")
    grouped = defaultdict(list)
    with counts_file.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            stem = row["source_log"].removesuffix(".log")
            case, _run = stem.rsplit("_", 1)
            grouped[case].append(int(row["race_warning_count"]) > 0)
    order = ["docker_27037_buggy", "docker_27037_fixed", "docker_25384_buggy", "docker_25384_fixed"]
    labels = {
        "docker_27037_buggy": "#27037 · buggy",
        "docker_27037_fixed": "#27037 · fixed",
        "docker_25384_buggy": "#25384 · buggy",
        "docker_25384_fixed": "#25384 · fixed",
    }
    return [(labels[key], sum(grouped[key]), len(grouped[key])) for key in order]


def draw_counts(ax, rows, title, subtitle, color):
    labels = [label for label, _, _ in rows]
    detected = [value for _, value, _ in rows]
    totals = [total for _, _, total in rows]
    positions = range(len(rows))
    ax.barh(positions, totals, color=PALE, height=0.5)
    ax.barh(positions, detected, color=color, height=0.5)
    for position, (value, total) in enumerate(zip(detected, totals)):
        ax.text(total + max(totals) * 0.04, position, f"{value}/{total}", va="center",
                fontsize=9, fontweight="semibold")
    ax.set_yticks(list(positions), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max(totals) * 1.25)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold", pad=16)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color="#5B6770", fontsize=8.5)
    ax.set_xlabel("Detected count")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#DDE5EA", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("counts", type=Path, help="race_warning_counts.tsv or its directory")
    args = parser.parse_args()

    paper = [
        ("Traditional", 7, 13),
        ("Anonymous function", 3, 4),
        ("Library", 0, 2),
        ("Channel misuse", 0, 1),
        ("Total", 10, 20),
    ]
    ours = load_team_counts(args.counts)

    plt.rcParams.update({
        "font.size": 9.2,
        "axes.titlesize": 12,
        "axes.labelcolor": TEXT,
        "text.color": TEXT,
        "xtick.color": "#5B6770",
        "ytick.color": TEXT,
        "pdf.fonttype": 42,
    })

    fig, (left, right) = plt.subplots(1, 2, figsize=(8.6, 3.7), layout="constrained")
    draw_counts(left, paper, "Paper benchmark", "Table 12 · distinct bugs detected within 100 runs", NAVY)
    draw_counts(right, ours, "Our reproduction", "Go 1.10.8 · runs containing at least one warning", TEAL)
    fig.legend(
        handles=[Patch(color=TEAL, label="Detected"), Patch(color=PALE, label="Tested but not detected")],
        loc="lower center", frameon=False, ncol=2, bbox_to_anchor=(0.5, -0.08),
    )

    output = Path(__file__).resolve().parents[1] / "report/figures/race_detection.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
