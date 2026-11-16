import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def draw_counts(ax, rows, title, xlabel, limit, color):
    for position, (label, detected, total) in enumerate(rows):
        ax.barh(position, total, color="#E8EDF2", height=0.55)
        ax.barh(position, detected, color=color, height=0.55)
        ax.text(total + 0.04 * limit, position, f"{detected}/{total}",
                va="center", fontsize=9)
    ax.set_yticks(range(len(rows)), [label for label, _, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, limit)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.spines[["top", "right", "left"]].set_visible(False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path, help="Directory containing the run logs")
    args = parser.parse_args()

    # Tu et al., Table 12. A bug counts once if detected within 100 runs.
    paper = [
        ("Traditional", 7, 13),
        ("Anonymous function", 3, 4),
        ("Library", 0, 2),
        ("Channel misuse", 0, 1),
        ("Total", 10, 20),
    ]
    ours = []
    for case in ("27037", "25384"):
        for version in ("buggy", "fixed"):
            logs = sorted(args.run_dir.glob(f"docker_{case}_{version}_*.log"))
            if not logs:
                parser.error(f"No logs found for Docker #{case} ({version})")
            detected = sum(
                "WARNING: DATA RACE" in log.read_text(encoding="utf-8")
                for log in logs
            )
            ours.append((f"Docker #{case} · {version}", detected, len(logs)))

    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.6), layout="constrained")
    draw_counts(left, paper, "Paper · Table 12", "Non-blocking bugs detected", 25, "#345D91")
    draw_counts(right, ours, "Our reproduction · Go 1.10.8",
                "Runs with a race warning", 4, "#247568")
    output = Path(__file__).resolve().parents[1] / "report/figures/race_detection.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
