# Extension Experiment: Old Bugs on a Modern Go Toolchain

Owner: WANG Jiuzhou (Block 4)

## Question

Our main reproduction runs on Go 1.10.8. **Do the same four bugs still trigger,
and are they still caught or missed by Go's built-in detectors, on a modern Go
toolchain?** The most interesting case is the closure data race of Figure 8
(Docker #27037), because Go 1.22 changed the language rule that causes it.

## Background: the Go 1.22 loop variable change

Before Go 1.22, a `for` loop has **one** variable `i` shared by all iterations.
A goroutine started with `go func() { ... i ... }()` reads that shared variable
while the loop keeps writing it, which is exactly the race in
`bugs/shared_memory/docker_race/docker_race.go`. That file uses a short
declaration (`for i := 17; i <= 20; i++`) and captures `i` by closure, not by
passing a copy. The patched control in `fixed/main.go` uses `go func(i int)
{ ... }(i)`, so it does not depend on the language rule.

Since Go 1.22, each iteration gets **its own** `i`. The change is controlled by
the language version in `go.mod`, not by the toolchain alone:

- `go.mod` says `go 1.21` or lower: old shared-variable rule, even on a new toolchain.
- `go.mod` says `go 1.22` or higher: new per-iteration rule.

A new toolchain therefore lets us switch only the language rule and keep
everything else fixed.

## Configurations

All three configurations use the same Ubuntu 18.04.6 linux/amd64 base, the
same host, the same copied bug sources, the same test commands, the same
`-race` policy as the main suite (channel tests without `-race`, shared-memory
tests with `-race`), `-count=1`, the same timeouts, `CGO_ENABLED=1`, and
unset `GOMAXPROCS`.

| Config | Image | Go toolchain | Language version | What it isolates |
|---|---|---|---|---|
| A | `cs340-go-bugs` (repo-root `Dockerfile`) | go1.10.8 linux/amd64 | none (GOPATH mode) | Paper-era baseline, re-run on this host |
| B | `cs340-go-bugs-modern` | go1.23.12 linux/amd64 | `go 1.21` in `go.mod` | Newer toolchain and runtime only (A vs B) |
| C | `cs340-go-bugs-modern` | go1.23.12 linux/amd64 (same binary as B) | `go 1.22` in `go.mod` | Loop-variable rule only (B vs C) |

Pinned modern toolchain (official tarball, checksum verified during the image
build):

- Version: **go1.23.12 linux/amd64**
- URL: https://go.dev/dl/go1.23.12.linux-amd64.tar.gz
- SHA256: `d3847fef834e9db11bf64e3fb34db9c04db14e068eeb064f49af747010454f90`
- Image environment: `GOTOOLCHAIN=local`, `GOPROXY=off`, `GOSUMDB=off`, `CGO_ENABLED=1`

The runner copies the files under `bugs/` into `extension/workspace/` and
never edits `bugs/`. Config A has no `go.mod`. Configs B and C write a
generated `go.mod` (`module cs340/extension`) with the language version
above. `go list -m` recorded `cs340/extension 1.21` under B and
`cs340/extension 1.22` under C. Every test is invoked from
`extension/workspace` so the module file, when present, is honored.

## How to reproduce

From the repository root, with Docker available:

```bash
# Baseline image: Ubuntu 18.04 + Go 1.10.8
docker build --platform linux/amd64 -t cs340-go-bugs .

# Modern image: same Ubuntu 18.04 + Go 1.23.12 (checksum-pinned)
docker build --platform linux/amd64 \
  -f extension/Dockerfile.modern \
  -t cs340-go-bugs-modern \
  extension/

# Official comparison: 6 cases x 3 configs x 10 runs
REPEATS=10 bash extension/run_extension.sh
```

`extension/run_extension.sh` launches config A in `cs340-go-bugs` and configs
B and C in `cs340-go-bugs-modern`, writes raw logs and summaries under
`extension/results/run-<timestamp>/`, and runs `extension/summarize_extension.py`.
Override `REPEATS`, `BASE_IMAGE`, or `MODERN_IMAGE` if needed. The generated
`extension/workspace/` directory is local scaffolding and is gitignored.

## Official run on this host

Evidence directory:

```
extension/results/run-20261118T115819Z-IAbvyc/
```

The same per-run table is also stored as `report/data/extension_record.csv`.

Host and container (see `environment.txt` in that directory):

- Host: Debian GNU/Linux 13.7 (trixie), kernel 6.12.113+, x86_64, 8 CPUs, Docker 29.10.0. Native amd64; no QEMU / Rosetta emulation.
- Both images: Ubuntu 18.04.6 LTS, GCC 7.5.0, `CGO_ENABLED=1`, `GORACE=exitcode=66`, `GOMAXPROCS` unset (defaults to 8).
- Baseline image id: `sha256:789cdfc2df686d788cbdd18fdb291b84aaad5c6a27d3c37485e4df139f28e43b`
- Modern image id: `sha256:eac4a3805fc657fa1de2cf38454571074d6e8b9b718e3818f70e7f6be1c50f08`
- Worktree base commit recorded at the start of the run: `132ca4c702b2872f2b855b1ad27f5058af2f8587`
- Started: 18 Nov 2026, 19:58:19 (UTC+8, Asia/Shanghai)

Each case was run 10 times per configuration (180 tests). Metrics per run:
manifestation, `race_report` (`WARNING: DATA RACE`), `deadlock_report`
(`all goroutines are asleep - deadlock`), wall-clock duration, command exit
code, official checker verdict, and the printed version multiset for Figure 8.

## What was actually observed

The hypotheses were treated as predictions, not as results. The official
Week 2 checkers were still used, so under config C the Figure 8 buggy case is
classified `UNEXPECTED_OR_NOT_REPRODUCED` when the test **passes** without a
race: that is the intended scientific outcome, not a harness failure.

| Case | Config A (go1.10.8, GOPATH) | Config B (go1.23.12, `go 1.21`) | Config C (go1.23.12, `go 1.22`) |
|---|---|---|---|
| Kubernetes #5316 (blocking leak) | `EXPECTED_BLOCKING` 10/10; timeout; no deadlock report | Same 10/10 | Same 10/10 |
| Docker #24007 (double close) | `EXPECTED_PANIC` 10/10 | Same 10/10 | Same 10/10 |
| Docker #25384 buggy (WaitGroup) | `EXPECTED_BLOCKING` 10/10; timeout in `Wait()`; no deadlock report; no race warning | Same 10/10 | Same 10/10 |
| Docker #25384 fixed | `FIXED_PASS` 10/10 | Same 10/10 | Same 10/10 |
| Docker #27037 buggy (Figure 8) | `EXPECTED_RACE` 10/10; race warning 10/10; never the unique `{v1.17..v1.20}` set | `EXPECTED_RACE` 10/10; race warning 10/10; all 10 runs printed a single repeated value | Official checker 0/10 (`UNEXPECTED_OR_NOT_REPRODUCED`); test exit 0; race warning 0/10; unique `{v1.17..v1.20}` 10/10 |
| Docker #27037 fixed | `FIXED_PASS` 10/10; unique versions 10/10; no race warning | Same 10/10 | Same 10/10 |

No log among the 180 official runs contains `all goroutines are asleep - deadlock`.
Absence of a race warning is not by itself proof that there is no race; for
Figure 8, config C additionally printed each of `v1.17`–`v1.20` once in every
run, which is the behavior of the per-iteration rule. Wall-clock standard
deviations on B and C for the first package in a module (Docker #24007 and
the first `-race` compile of Docker #25384) are dominated by one cold compile,
not by scheduling. After the first run, those blocking cases sit on the 5s
test timeout just as they do under config A. Timing differences are **not**
used to claim a scheduler-mechanism effect.

Config A on this 8-CPU host reproduced the same official-checker symptoms as
the earlier WSL2 (16-CPU) Week 2 run. Those WSL2 numbers are context only;
the paired baseline for A vs B vs C is this host's config A.

## Status

- [x] Week 1: first plan
- [x] Week 2: detailed design with three configs and hypotheses
- [x] Modern Go Docker image and run script
- [x] Raw logs and filled records (`N=10`, go1.23.12, official evidence directory above)
- [x] Results table in `report/sections/extension.tex` and deviation notes in `report/sections/analysis.tex`
