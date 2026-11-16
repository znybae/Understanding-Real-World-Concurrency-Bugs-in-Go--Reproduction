# Extension Experiment Plan: Old Bugs on a Modern Go Toolchain

Owner: WANG Jiuzhou (Block 4)

## Question

Our main reproduction runs on Go 1.10.8. **Do the same four bugs still trigger, and are
they still caught or missed by Go's built-in detectors, on a modern Go toolchain?**
The most interesting case is the closure data race of Figure 8 (Docker #27037), because
Go 1.22 changed the language rule that causes it.

## Background: the Go 1.22 loop variable change

Before Go 1.22, a `for` loop has **one** variable `i` shared by all iterations. A goroutine
started with `go func() { ... i ... }()` reads that shared variable while the loop keeps
writing it, which is exactly the race in `bugs/shared_memory/docker_race/docker_race.go`.

Since Go 1.22, each iteration gets **its own** `i`. The change is controlled by the
language version in `go.mod`, not by the toolchain alone:

- `go.mod` says `go 1.21` or lower: old shared-variable rule, even on a new toolchain.
- `go.mod` says `go 1.22` or higher: new per-iteration rule.

So a new toolchain lets us switch only the language rule and keep everything else fixed.

## Hypotheses

| Case | Expected on Go 1.10.8 | Expected on modern Go, `go 1.21` | Expected on modern Go, `go 1.22` |
|---|---|---|---|
| Figure 8, Docker #27037 (closure race) | `DATA RACE` reported | `DATA RACE` reported | No race; prints `v1.17` to `v1.20` once each |
| Figure 5, Docker #25384 (WaitGroup) | Blocks; runtime deadlock report in `go run` | Same | Same |
| Figure 1, Kubernetes #5316 (leak) | Goroutine stays blocked; no detector fires | Same | Same |
| Figure 10, Docker #24007 (double close) | `panic: close of closed channel` | Same | Same |

Only Figure 8 should change. The other three serve as controls: if they also change, the
cause is the toolchain or runtime, not the loop variable rule.

## Design: one factor at a time

Three configurations, all in the same Ubuntu 18.04 base image on the same machine:

| Config | Go toolchain | `go.mod` language version | What it isolates |
|---|---|---|---|
| A (baseline) | 1.10.8 | none (GOPATH mode) | Paper-era behavior, same as main reproduction |
| B | 1.22 or later, exact patch pinned | `go 1.21` | Effect of the newer toolchain and runtime alone (A vs B) |
| C | same as B | `go 1.22` | Effect of the loop variable rule alone (B vs C) |

Kept identical across A, B and C: base image, hardware, bug source files (not edited),
test commands, `-race`, `-count=1`, timeouts, and `GOMAXPROCS`.

Notes:

- Go 1.10.8 has no module support, so A has no `go.mod`. B and C need one. The extension
  copies the bug files into `extension/workspace/` with a generated `go.mod`, so the files
  under `bugs/` stay untouched for the main experiment.
- Optional sanity check: Go 1.21 offered the new rule as a preview through
  `GOEXPERIMENT=loopvar`. If time allows, run Go 1.21 with and without it as a second way
  to isolate the rule.

## Metrics

Recorded per case, per config, per run, using the same columns as
`report/data/test_record.csv` (`go_version` tells the configs apart):

1. Bug manifests or not (blocking, panic, duplicated values, timeout).
2. `race_report`: output contains `WARNING: DATA RACE`.
3. `deadlock_report`: output contains `all goroutines are asleep - deadlock`.
4. For Figure 8: the set of printed versions (duplicates mean the race changed the result).

Each case runs at least 10 times per config, because race detection and the printed values
depend on scheduling. We report how many of N runs detected the race and the mean ± standard
deviation of the run time.

## Planned steps

1. **Week 2 (this week):** finalize this plan and the test record template. ✅
2. **Week 3:** add `extension/Dockerfile.modern` (same Ubuntu 18.04 base, Go version passed
   as a build argument) and `extension/run_extension.sh`, which copies the bug files,
   writes `go.mod` for B or C, runs every case N times and saves raw logs.
3. **Week 4:** fill the records, draw a chart of detection rate per config, and write the
   Extension section of the report against claim C3 (race detector coverage).

## Risks

- Race detection depends on the actual interleaving, so a missing report in one run does
  not prove there is no race. Using N ≥ 10 runs reduces this.
- The amd64 image runs under emulation on Apple Silicon, which changes timing. All three
  configs run on the same host, so the comparison stays fair.

## Status

- [x] Week 1: first plan
- [x] Week 2: detailed design with three configs and hypotheses
- [ ] Modern Go Docker image and run script
- [ ] Raw logs and filled records
- [ ] Results table and figure in the report
