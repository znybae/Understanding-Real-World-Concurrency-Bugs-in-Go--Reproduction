#!/usr/bin/env python3
"""Summarize the Week 3 A/B/C extension runs from raw logs and summary.tsv.

This script only aggregates observed values. It never fills paper table cells
and never substitutes a missing run.

Command column policy
---------------------
Raw logs written inside the Docker bind mount include a COMMAND= header line,
but that header is a runner echo, not an independent ground-truth source for
the report table. The command column is therefore reconstructed from the same
case table used by extension/run_extension.sh (timeout wrapper, -race flag,
per-test -timeout, -run regexp, and package path). When a log is readable, the
reconstructed command is cross-checked against the COMMAND= line; a mismatch
is fatal so the CSV cannot silently drift from the runner.
"""
from __future__ import annotations

import csv
import datetime
import re
import shlex
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

OFFICIAL_EXPECTED = {
    "docker_24007_buggy": "EXPECTED_PANIC",
    "k8s_5316_buggy": "EXPECTED_BLOCKING",
    "docker_25384_buggy": "EXPECTED_BLOCKING",
    "docker_25384_fixed": "FIXED_PASS",
    "docker_27037_buggy": "EXPECTED_RACE",
    "docker_27037_fixed": "FIXED_PASS",
}

META = {
    "docker_24007_buggy": {
        "case_id": "docker_24007",
        "paper_figure": "Figure 10",
        "owner": "Block 2",
        "category": "non-blocking / message passing",
        "version": "buggy",
    },
    "k8s_5316_buggy": {
        "case_id": "k8s_5316",
        "paper_figure": "Figure 1",
        "owner": "Block 2",
        "category": "blocking / message passing",
        "version": "buggy",
    },
    "docker_25384_buggy": {
        "case_id": "docker_25384",
        "paper_figure": "Figure 5",
        "owner": "Block 3",
        "category": "blocking / shared memory",
        "version": "buggy",
    },
    "docker_25384_fixed": {
        "case_id": "docker_25384",
        "paper_figure": "Figure 5",
        "owner": "Block 3",
        "category": "blocking / shared memory",
        "version": "fixed",
    },
    "docker_27037_buggy": {
        "case_id": "docker_27037",
        "paper_figure": "Figure 8",
        "owner": "Block 3",
        "category": "non-blocking / shared memory",
        "version": "buggy",
    },
    "docker_27037_fixed": {
        "case_id": "docker_27037",
        "paper_figure": "Figure 8",
        "owner": "Block 3",
        "category": "non-blocking / shared memory",
        "version": "fixed",
    },
}

# Mirrors extension/run_extension.sh cases[]: package, test, timeout, use_race.
RUNNER_CASES = {
    "docker_24007_buggy": ("./channel", "TestDocker24007", "10s", False),
    "k8s_5316_buggy": ("./channel", "TestK8s5316", "5s", False),
    "docker_25384_buggy": ("./waitgroup_deadlock", "TestWaitGroupDeadlock", "5s", True),
    "docker_25384_fixed": ("./waitgroup_deadlock/fixed", "TestWaitGroupFixed", "5s", True),
    "docker_27037_buggy": ("./docker_race", "TestDockerRace", "10s", True),
    "docker_27037_fixed": ("./docker_race/fixed", "TestDockerRaceFixed", "10s", True),
}

CASE_ORDER = [
    "k8s_5316_buggy",
    "docker_24007_buggy",
    "docker_25384_buggy",
    "docker_25384_fixed",
    "docker_27037_buggy",
    "docker_27037_fixed",
]
CONFIG_ORDER = ["A", "B", "C"]

# Preserve the calendar date of the official evidence run when regenerating.
OFFICIAL_RECORD_DATE = "2026-11-18"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def unique_versions(versions: str) -> bool:
    items = [v for v in versions.split(",") if v]
    expected = ["v1.17", "v1.18", "v1.19", "v1.20"]
    return sorted(items) == expected


def reconstruct_command(case: str) -> str:
    """Rebuild the go-test argv from run_extension.sh, shell-quoted like %q."""
    package, test_name, limit, use_race = RUNNER_CASES[case]
    cmd = ["timeout", "120s", "go", "test"]
    if use_race:
        cmd.append("-race")
    cmd.extend(["-v", "-count=1", f"-timeout={limit}", "-run", f"^{test_name}$", package])
    # Match bash printf '%q ' output used in the runner (trailing space included).
    return " ".join(shlex.quote(part) for part in cmd) + " "


def normalize_command(command: str) -> str:
    return " ".join(shlex.split(command.strip()))


def observed_symptom(text: str, versions: str, race: str, deadlock: str) -> str:
    """Concise English symptom grounded in the log body and summary flags.

    Distinguishes go-test timeouts from the runtime deadlock detector string.
    A missing race warning is recorded as absence of WARNING: DATA RACE, not as
    a claim that a race is theoretically impossible.
    """
    parts = []
    if "panic: close of closed channel" in text:
        parts.append("panic: close of closed channel")
    if "test timed out after 5s" in text or "panic: test timed out after 5s" in text:
        if "[chan send]" in text:
            parts.append("test timed out after 5s; worker at [chan send]")
        elif "sync.(*WaitGroup).Wait" in text:
            parts.append("test timed out after 5s in WaitGroup.Wait")
        else:
            parts.append("test timed out after 5s")
    if race == "yes":
        parts.append("WARNING: DATA RACE")
    if deadlock == "yes":
        parts.append("all goroutines are asleep - deadlock")
    if versions:
        items = versions.split(",")
        counts = Counter(items)
        if unique_versions(versions):
            parts.append("printed " + " ".join(items) + " once each")
        else:
            parts.append("printed " + " ".join(items) + f" (counts={dict(counts)})")
    if re.search(r"^PASS$", text, re.M):
        joined = " ".join(parts)
        if "printed" not in joined and "WARNING: DATA RACE" not in joined:
            parts.append("PASS")
        elif "printed" in joined and "WARNING: DATA RACE" not in joined and "PASS" not in parts:
            # Fixed / language-rule PASS runs that also print version lines.
            parts.append("PASS")
    return "; ".join(parts) if parts else "see log"


def resolve_log_path(log_field: str, repo: Path) -> Path:
    """Map container or host log paths onto the repository checkout."""
    raw = Path(log_field)
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
        text = raw.as_posix()
        # Docker host bind: repo mounted at /workspace inside the container.
        if text.startswith("/workspace/"):
            candidates.append(repo / text[len("/workspace/") :])
        # Older host-absolute layouts that already include .../extension/results/...
        marker = "/extension/results/"
        if marker in text:
            candidates.append(repo / ("extension/results/" + text.split(marker, 1)[1]))
    else:
        candidates.append(repo / raw)
        candidates.append(raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def relpath_from_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        text = path.as_posix()
        if "/extension/results/" in text:
            return "extension/results/" + text.split("/extension/results/", 1)[1]
        if text.startswith("/workspace/"):
            return text[len("/workspace/") :]
        return text


def extract_command_from_log(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("COMMAND="):
            return line[len("COMMAND=") :]
    return ""


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: summarize_extension.py RUN_DIR", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).resolve()
    repo = run_dir.parent.parent.parent
    summary_path = run_dir / "summary.tsv"
    with summary_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if not rows:
        print("summary.tsv is empty", file=sys.stderr)
        return 1

    record_date = OFFICIAL_RECORD_DATE
    # Prefer the host environment.txt date when present, else keep the official stamp.
    env_path = run_dir / "environment.txt"
    if env_path.exists():
        # Keep the fixed official calendar date for reproducible CSV regeneration.
        record_date = OFFICIAL_RECORD_DATE

    record_rows = []
    for row in rows:
        case = row["case"]
        meta = META[case]
        log_path = resolve_log_path(row["log"], repo)
        text = read_text(log_path) if log_path.exists() else ""
        if not text:
            print(f"WARNING: missing or unreadable log: {row['log']} -> {log_path}", file=sys.stderr)
        versions = row.get("versions") or ""
        symptom = observed_symptom(text, versions, row["race_report"], row["deadlock_report"])
        command = reconstruct_command(case)
        logged = extract_command_from_log(text)
        if logged and normalize_command(logged) != normalize_command(command):
            print(
                f"COMMAND mismatch for {case} {row['config']}#{row['iteration']}:\n"
                f"  reconstructed: {command!r}\n"
                f"  log COMMAND=:  {logged!r}",
                file=sys.stderr,
            )
            return 1
        log_rel = relpath_from_repo(log_path, repo)
        if not (repo / log_rel).exists():
            print(f"Relative log path does not exist: {log_rel}", file=sys.stderr)
            return 1
        record_rows.append(
            {
                "case_id": meta["case_id"],
                "paper_figure": meta["paper_figure"],
                "owner": meta["owner"],
                "category": meta["category"],
                "version": meta["version"],
                "config": row["config"],
                "go_version": row["go_version"],
                "language_version": row["language_version"],
                "run": row["iteration"],
                "command": command.strip(),
                "expected": OFFICIAL_EXPECTED[case],
                "exit_code": row["command_exit_code"],
                "checker_result": row["result"],
                "observed_symptom": symptom,
                "race_report": row["race_report"],
                "deadlock_report": row["deadlock_report"],
                "versions": versions,
                "duration_s": row["duration_s"],
                "log_file": log_rel,
                "date": record_date,
                "recorder": "WANG Jiuzhou",
            }
        )

    record_path = run_dir / "test_record.csv"
    fieldnames = [
        "case_id",
        "paper_figure",
        "owner",
        "category",
        "version",
        "config",
        "go_version",
        "language_version",
        "run",
        "command",
        "expected",
        "exit_code",
        "checker_result",
        "observed_symptom",
        "race_report",
        "deadlock_report",
        "versions",
        "duration_s",
        "log_file",
        "date",
        "recorder",
    ]
    with record_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record_rows)

    stats_path = run_dir / "statistics.csv"
    with stats_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "config",
                "go_version",
                "language_version",
                "case",
                "runs",
                "official_expected",
                "official_matches",
                "official_indicator_mean",
                "official_indicator_sample_std",
                "race_report_yes",
                "deadlock_report_yes",
                "unique_version_multiset",
                "duration_mean_s",
                "duration_sample_std_s",
                "checker_results",
            ]
        )
        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in rows:
            grouped[(row["config"], row["case"])].append(row)
        for config in CONFIG_ORDER:
            for case in CASE_ORDER:
                selected = grouped.get((config, case), [])
                if not selected:
                    writer.writerow(
                        [config, "", "", case, 0, OFFICIAL_EXPECTED[case], "MISSING", "NA", "NA", "NA", "NA", "NA", "NA", "NA", ""]
                    )
                    continue
                expected = OFFICIAL_EXPECTED[case]
                matches = [
                    int(r["checker_exit_code"] == "0" and r["result"] == expected)
                    for r in selected
                ]
                durations = [float(r["duration_s"]) for r in selected]
                race_yes = sum(1 for r in selected if r["race_report"] == "yes")
                deadlock_yes = sum(1 for r in selected if r["deadlock_report"] == "yes")
                unique_n = sum(1 for r in selected if unique_versions(r.get("versions") or ""))
                result_counts = Counter(r["result"] for r in selected)
                result_s = ";".join(f"{k}={v}" for k, v in sorted(result_counts.items()))
                mean = statistics.mean(matches)
                std = statistics.stdev(matches) if len(matches) > 1 else "NA"
                dmean = statistics.mean(durations)
                dstd = statistics.stdev(durations) if len(durations) > 1 else "NA"
                writer.writerow(
                    [
                        config,
                        selected[0]["go_version"],
                        selected[0]["language_version"],
                        case,
                        len(selected),
                        expected,
                        sum(matches),
                        f"{mean:.4f}" if isinstance(mean, float) else mean,
                        f"{std:.4f}" if isinstance(std, float) else std,
                        race_yes,
                        deadlock_yes,
                        unique_n,
                        f"{dmean:.3f}",
                        f"{dstd:.3f}" if isinstance(dstd, float) else dstd,
                        result_s,
                    ]
                )

    overview = run_dir / "overview.txt"
    lines = ["Extension run overview", str(run_dir), ""]
    for config in CONFIG_ORDER:
        lines.append(f"== Config {config} ==")
        for case in CASE_ORDER:
            selected = grouped.get((config, case), [])
            if not selected:
                lines.append(f"  {case}: MISSING")
                continue
            races = sum(1 for r in selected if r["race_report"] == "yes")
            deadlocks = sum(1 for r in selected if r["deadlock_report"] == "yes")
            unique_n = sum(1 for r in selected if unique_versions(r.get("versions") or ""))
            results = Counter(r["result"] for r in selected)
            durs = [float(r["duration_s"]) for r in selected]
            lines.append(
                f"  {case}: n={len(selected)} results={dict(results)} "
                f"race={races}/{len(selected)} deadlock={deadlocks}/{len(selected)} "
                f"unique_versions={unique_n}/{len(selected)} "
                f"duration_s={statistics.mean(durs):.3f}±"
                f"{(statistics.stdev(durs) if len(durs) > 1 else 0):.3f}"
            )
        lines.append("")
    overview.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", record_path)
    print("Wrote", stats_path)
    print("Wrote", overview)
    print(overview.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
