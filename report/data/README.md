# Test record

`test_record.csv` is the template for tracking every reproduction run of Block 2
(`bugs/channel/`) and Block 3 (`bugs/shared_memory/`). One row is one run of one
case, version and Go toolchain. At least three runs per case are needed for the
report's mean and standard deviation.

Fill the result columns from a full-suite evidence directory produced by:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD:/workspace" -w /workspace \
  -e REPEATS=3 cs340-go-bugs bash scripts/run_all.sh
```

The runner writes `logs/full_suite/run-.../` (kept local), including
`summary.tsv`, `statistics.csv`, `environment.txt` and one `.log` per case and
iteration. The `command` and `expected` columns already match
`scripts/run_all.sh` on commit `72cb93d`.

Expected checker results:

| Case | Version | Checker result |
|---|---|---|
| `k8s_5316` (`TestK8s5316`) | buggy | `EXPECTED_BLOCKING` |
| `docker_24007` (`TestDocker24007`) | buggy | `EXPECTED_PANIC` |
| `docker_25384` (`TestWaitGroupDeadlock`) | buggy | `EXPECTED_BLOCKING` |
| `docker_25384` (`TestWaitGroupFixed`) | fixed | `FIXED_PASS` |
| `docker_27037` (`TestDockerRace`) | buggy | `EXPECTED_RACE` |
| `docker_27037` (`TestDockerRaceFixed`) | fixed | `FIXED_PASS` |

How to fill a row after a run:

| Column | What to write |
|---|---|
| `exit_code` | The `COMMAND_EXIT_CODE` printed by the checker |
| `checker_result` | `RESULT=...` from `bugs/channel/check_result.sh` or `bugs/shared_memory/check_result.sh` |
| `observed_symptom` | Short description, e.g. `test timed out after 5s; [chan send]`, `panic: close of closed channel`, `WARNING: DATA RACE` |
| `race_report` | `yes` if the output contains `WARNING: DATA RACE`, otherwise `no` |
| `deadlock_report` | `yes` if the output contains `all goroutines are asleep - deadlock`, otherwise `no` |
| `duration_s` | Run time reported by `go test` |
| `log_file` | Path of the raw log the row comes from, under `logs/full_suite/run-.../` |
| `date`, `recorder` | Date of the run and who ran it |

Do not invent values. Leave a cell empty until the corresponding log is in hand.
The same rows appear in `report/tables/test_record.tex` (Table "Test record").
The extension experiment uses the same columns with a different `go_version`.
