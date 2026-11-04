# Extension Experiment Plan

Owner: WANG Jiuzhou (Block 4)

## Question

The paper studies Go concurrency bugs with the Go toolchains of its time, and our main
reproduction runs in Go 1.10.8. Go has changed a lot since then. **Do the same bugs still
trigger, and are they still detected or missed by Go's built-in tools, under a modern Go
toolchain (1.23 or later)?**

This connects directly to the paper's claims about how well Go's built-in deadlock detector
and data race detector catch real bugs.

## Why a newer Go might behave differently

- **Per-iteration loop variables (Go 1.22).** Since Go 1.22, each loop iteration gets its own
  copy of the loop variable when the module's `go.mod` declares `go 1.22` or later. The
  paper's anonymous-function closure race (Figure 8, in `bugs/shared_memory/`) should
  disappear under the new semantics.
- **Asynchronous preemption (Go 1.14).** Goroutines can now be preempted at almost any
  point, which may change how often timing-dependent bugs show up.
- **Runtime and race detector updates.** The deadlock detector and the race detector have
  had many releases of changes since 1.10.

## Design (one factor at a time)

| Item | Baseline | Extension |
|---|---|---|
| Go toolchain | 1.10.8 | 1.23+ (exact version pinned in a Dockerfile) |
| Bug programs | same files from `bugs/` | same files, unchanged |
| Hardware | same machine | same machine |
| Trigger / judging | same scripts, same timeout | same scripts, same timeout |
| Runs | at least 3 (more for flaky bugs) | same |

Only the Go version changes. For the loop-variable case we also run a second controlled
variant where only the `go` directive in `go.mod` changes (for example `go 1.21` vs `go 1.22`)
on the same modern toolchain, to separate the language change from other runtime changes.

## Metrics

For each bug case and each Go version:

1. Whether the bug manifests (deadlock, panic, wrong result, or hang until timeout), and
   in how many of N runs.
2. Whether the built-in deadlock detector reports it (`fatal error: all goroutines are asleep`).
3. Whether `go run -race` / `go test -race` reports a data race.

## Planned steps

1. Add a second Docker image (or a build argument) for the modern Go version.
2. Write `extension/run_extension.sh` that runs every case in `bugs/` under both versions
   and writes raw logs to `results/extension/`.
3. Summarize the logs into a table and a chart for the report (Section "Extension").

## Status

- [x] Week 1: plan written
- [ ] Modern Go Docker image
- [ ] Run script and raw logs
- [ ] Results table and figure in the report
