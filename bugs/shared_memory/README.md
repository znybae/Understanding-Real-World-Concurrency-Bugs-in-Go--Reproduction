# Shared-Memory Bug Reproductions

Minimal reproductions based on Figures 5 and 8 of:
Tengfei Tu et al., "Understanding Real-World Concurrency Bugs in Go",
ASPLOS 2019.

Paper: https://songlh.github.io/paper/go-study.pdf
Authors' repository: https://github.com/system-pclub/go-concurrency-bugs

## Scope and environment

These examples recreate the concurrency patterns shown in the paper.
They do not run the full Docker application or reproduce the paper's
aggregate bug statistics.

Environment: Ubuntu 18.04.6, Go 1.10.8, linux/amd64,
GCC 7.5.0, CGO_ENABLED=1.
The amd64 container runs on an Apple M2 Mac through Docker Desktop.
See environment.txt for the recorded container environment.

Run the commands below from bugs/shared_memory inside the container.
See the section below for setup using the team's shared Dockerfile.

## Figure 5: WaitGroup blocking

Directory: waitgroup_deadlock/

The buggy version registers two tasks but calls Wait inside the loop.
The first task finishes, but the second task cannot start.
The fix moves Wait outside the loop.

Run the buggy program:
    timeout 60s go run waitgroup_deadlock/waitgroup_deadlock.go

Expected: a runtime deadlock report and a nonzero exit status.

Run the buggy test:
    timeout 120s go test -race -v -count=1 -timeout=5s ./waitgroup_deadlock

Expected: test timeout, with a stack trace showing WaitGroup.Wait.
The race detector is not a general deadlock detector.

Run the fixed test:
    timeout 120s go test -race -v -count=1 -timeout=5s ./waitgroup_deadlock/fixed

Expected: both tasks complete and the test passes.

## Figure 8: Closure data race

Directory: docker_race/

Under Go 1.10, the parent updates the loop variable i while child
goroutines read the same variable through a closure.
The fix passes i to each goroutine as a value parameter.

Run the buggy test:
    timeout 120s go test -race -v -count=1 -timeout=10s ./docker_race

Expected when detected: WARNING: DATA RACE and a failing test.
Detection and printed values may vary across runs.

Run the fixed test:
    timeout 120s go test -race -v -count=1 -timeout=10s ./docker_race/fixed

Expected: v1.17 through v1.20 once each, in any order, and a passing test.

## Evidence and deviations

Logs are stored in each case's logs/ directory.
Initial runs observed blocking in Figure 5 and a race in Figure 8;
both fixed versions passed their race-enabled tests.

Business logic and dependencies were removed.
Figure 5 uses two simple tasks instead of Docker plugins.
Figure 8 retains the loop and version-string construction.
WaitGroup synchronization, progress output, test wrappers and timeout
limits were added for execution and observation.

These are initial single-run observations, not detection-rate estimates.
The intentionally buggy tests are expected to fail or time out.
Run cases separately rather than treating go test ./... as a passing suite.

## Using the team's Docker image

Run these commands from the repository root on the host computer.

Build the image:

    docker build --platform linux/amd64 -t cs340-go-bugs .

Start the container with the repository mounted:

    docker run --rm -it --platform linux/amd64 -v "$PWD:/workspace" -w /workspace/bugs/shared_memory cs340-go-bugs bash

Then run the case commands above inside the container.

The initial logs were collected using a manually configured container.
Validation using the team's Docker image is complete for one run per case:

| Case | Observed result | Exit code | Log |
| --- | --- | --- | --- |
| WaitGroup buggy | Test timeout; blocked in WaitGroup.Wait | 1 | waitgroup_deadlock/logs/team_buggy_race_test_01.log |
| WaitGroup fixed | PASS | 0 | waitgroup_deadlock/logs/team_fixed_race_test_01.log |
| Closure buggy | DATA RACE detected | 1 | docker_race/logs/team_buggy_race_test_01.log |
| Closure fixed | PASS; no race reported | 0 | docker_race/logs/team_fixed_race_test_01.log |

These observations validate the minimal examples only.
Repeated-run statistics and aggregate paper results are not yet reproduced.

## Case identifiers and scope clarifications

- Figure 5: Docker/Moby #25384.
  Reference fix: 42360d164b9f25fb4b150ef066fcf57fa39559a7.
  Test filename: docker_25384_test.go.
- Figure 8: Docker/Moby #27037.
  Reference fix: 825e3a66a419038600024be7dfc5ca24426444f0.
  Test filename: docker_27037_test.go.

Figure 5 is a blocking shared-memory bug. It remains in this directory
according to the Week 1 ownership assignment.

For Figure 8, the original patch uses loop values 17 through 21.
Our reduced example uses 17 through 20, creating four goroutines.
This preserves the shared-loop-variable race mechanism but changes
the iteration count. Existing logs were collected with this reduced range.

Test files were renamed after the initial runs. Older logs therefore
contain the previous test filenames; they have not been edited.

## Batch execution

From the repository root, run three rounds in the shared Docker image:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD:/workspace" -w /workspace \
  -e REPEATS=3 cs340-go-bugs bash scripts/run_all.sh
```

The runner saves the raw output, environment details, input hashes,
per-run results, and summary statistics in a new local directory under
`logs/shared_memory/`. Keep generated logs local.

### Week 2 validation

On 2026-11-12, we ran the revised runner from base commit `75a90ac`
with Go 1.10.8 on Linux amd64. All 12 checks matched the expected outcomes.

| Case | Observed outcome | Runs matching expectation |
| --- | --- | --- |
| Figure 5, buggy | Test timed out after 5 s with `sync.(*WaitGroup).Wait` in the stack | 3/3 |
| Figure 5, fixed | Both tasks completed and the test passed | 3/3 |
| Figure 8, buggy | The race detector reported `WARNING: DATA RACE` | 3/3 |
| Figure 8, fixed | Each version from `v1.17` to `v1.20` appeared once and the test passed | 3/3 |

For each case, the binary indicator for matching the expected outcome
had a mean of 1.00 and a sample standard deviation of 0.00 across three
runs. These statistics describe the four minimal test cases.

Local evidence directory: `logs/shared_memory/run-20261112T094618Z-7ysnoJ/`.