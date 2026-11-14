# Channel Bug Reproductions

These are minimal models based on Figures 1 and 10 of
"Understanding Real-World Concurrency Bugs in Go" (ASPLOS 2019).

Sources:
- https://songlh.github.io/paper/go-study.pdf
- https://github.com/system-pclub/go-concurrency-bugs

## Environment

Run from /workspace in the shared Docker container:
Ubuntu 18.04, Go 1.10.8, linux/amd64.

## Docker #24007: concurrent close

```bash
go test -v -count=1 -timeout=10s -run '^TestDocker24007$' ./bugs/channel
```

Expected: a nonzero exit status and `panic: close of closed channel`.

Both workers are forced into the default branch before either closes
the channel. The second close causes an unrecovered panic.
This is a non-blocking channel misuse bug.

## Kubernetes #5316: blocked sender after timeout

```bash
go test -v -count=1 -timeout=5s -run '^TestK8s5316$' ./bugs/channel
```

Expected: a nonzero exit status, `test timed out after 5s`, and a
worker stack marked `[chan send]` at `result <- 42`.

The worker is held until the parent times out. It then sends to an
unbuffered channel with no receiver. A test-only wait keeps the
process alive until the test timeout exposes the blocked worker.
This models a goroutine leak, not necessarily an application-wide deadlock.

## Interpretation and integration

Run the cases separately: an unrecovered panic stops the test process,
so one command running both tests may not exercise both cases.

A nonzero exit status alone is insufficient evidence. Check the
expected panic message or the timeout together with the blocked-send
stack. Compilation and environment errors are not successful reproductions.

The execution order is controlled. These tests demonstrate bug
mechanisms, not natural triggering probabilities or full application
reproductions.

The infrastructure owner will integrate the commands into
scripts/run_all.sh. Runtime logs remain local and must not be committed.