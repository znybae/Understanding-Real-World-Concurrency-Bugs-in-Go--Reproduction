import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


NAVY = "#244B6B"
TEAL = "#18838B"
AMBER = "#D18B2C"
PALE = "#E4EBEF"
TEXT = "#24323B"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path, help="Path to report/data/test_record.csv")
    args = parser.parse_args()

    grouped = defaultdict(list)
    with args.records.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            if row["case_id"] in {"docker_25384", "docker_27037"}:
                grouped[(row["case_id"], row["version"])].append(row)

    keys = [
        ("docker_25384", "buggy"),
        ("docker_25384", "fixed"),
        ("docker_27037", "buggy"),
        ("docker_27037", "fixed"),
    ]
    labels = ["#25384 · buggy", "#25384 · fixed", "#27037 · buggy", "#27037 · fixed"]
    matches, timeouts, races, totals = [], [], [], []
    for key in keys:
        rows = grouped[key]
        totals.append(len(rows))
        matches.append(sum(row["checker_result"] == row["expected"] for row in rows))
        timeouts.append(sum("timed out" in row["observed_symptom"].lower() for row in rows))
        races.append(sum(row["race_report"].lower() == "yes" for row in rows))

    plt.rcParams.update({
        "font.size": 9.2,
        "axes.titlesize": 12,
        "axes.labelcolor": TEXT,
        "text.color": TEXT,
        "xtick.color": "#5B6770",
        "ytick.color": TEXT,
        "pdf.fonttype": 42,
    })
    fig, (left, right) = plt.subplots(1, 2, figsize=(8.6, 3.6), layout="constrained")
    positions = list(range(len(keys)))

    colors = [NAVY, TEAL, NAVY, TEAL]
    left.barh(positions, totals, color=PALE, height=0.5)
    left.barh(positions, matches, color=colors, height=0.5)
    for position, (value, total) in enumerate(zip(matches, totals)):
        left.text(total + 0.12, position, f"{value}/{total}", va="center", fontweight="semibold")
    left.set_title("Expected outcome", loc="left", color=NAVY, fontweight="bold", pad=15)
    left.text(0, 1.02, "Official checker matches", transform=left.transAxes, color="#5B6770", fontsize=8.5)
    left.set_xlim(0, 3.8)

    height = 0.34
    right.barh([p - height / 2 for p in positions], timeouts, height=height, color=AMBER, label="Test timeout")
    right.barh([p + height / 2 for p in positions], races, height=height, color=TEAL, label="Race warning")
    for position, (timeout, race) in enumerate(zip(timeouts, races)):
        right.text(timeout + 0.08, position - height / 2, f"{timeout}/3", va="center", fontsize=8.5)
        right.text(race + 0.08, position + height / 2, f"{race}/3", va="center", fontsize=8.5)
    right.set_title("Observed detector signals", loc="left", color=NAVY, fontweight="bold", pad=15)
    right.text(0, 1.02, "Signals are not interchangeable", transform=right.transAxes, color="#5B6770", fontsize=8.5)
    right.set_xlim(0, 3.8)
    right.legend(loc="lower right", frameon=False, fontsize=8.5)

    for ax in (left, right):
        ax.set_yticks(positions, labels)
        ax.invert_yaxis()
        ax.set_xlabel("Runs")
        ax.set_xticks([0, 1, 2, 3])
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#DDE5EA", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left", "bottom"]].set_visible(False)

    output = Path(__file__).resolve().parents[1] / "report/figures/shared_memory_comparison.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
