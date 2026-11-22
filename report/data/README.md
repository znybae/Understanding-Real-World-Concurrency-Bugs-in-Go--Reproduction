# Test records and official logs

`test_record.csv` records every official Week 2 reproduction run of Block 2
(`bugs/channel/`) and Block 3 (`bugs/shared_memory/`). One row is one run of one
case and version. The result columns were filled from

`report/results/week2_full_suite/run-20261114T075540Z-JMQOiG/`

which is the official evidence directory produced by Block 1 on 14 Nov 2026
with:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD:/workspace" -w /workspace \
  -e REPEATS=3 cs340-go-bugs bash scripts/run_all.sh
```

`statistics.csv` in that directory reports a mean of 1.00 and a sample standard
deviation of 0.00 for the binary expected-outcome indicator of every case.
Those statistics are not run times and are not the paper's aggregate detection
rates.

The same rows appear in `report/tables/test_record.tex`.

`extension_record.csv` records the official Week 3 modern-Go comparison
(configs A, B, and C; 10 independent runs per case per config; 180 rows).
It uses the same core columns as `test_record.csv`, plus `config`,
`language_version`, and the Figure 8 `versions` multiset. The numbers come
from

`extension/results/run-20261118T115819Z-IAbvyc/`

produced on 18 Nov 2026 (UTC+8, Asia/Shanghai) by:

```bash
docker build --platform linux/amd64 -t cs340-go-bugs .
docker build --platform linux/amd64 \
  -f extension/Dockerfile.modern \
  -t cs340-go-bugs-modern extension/
REPEATS=10 bash extension/run_extension.sh
```

The same summary appears in `report/tables/extension_record.tex`.
Configuration A on that host is the paired baseline; it is not a copy of the
Week 2 WSL2 numbers.


For `extension_record.csv`, the `command` column is reconstructed from the case
table in `extension/run_extension.sh` (the same `timeout` / `go test` argv the
runner builds). It is cross-checked against each log's `COMMAND=` header when the
log is readable, but the report value is the reconstructed runner command, not a
claim that the log itself is the authoritative source of that field. The
`log_file` column stores a repository-relative path under
`extension/results/run-20261118T115819Z-IAbvyc/`. The `observed_symptom` column is
a short English summary taken from the log body (for example a 5s test timeout at
`[chan send]` versus `WaitGroup.Wait`); it is not the Go runtime deadlock
detector string unless that string actually appears. Re-running
`python3 extension/summarize_extension.py extension/results/run-20261118T115819Z-IAbvyc`
regenerates `test_record.csv` with the same rules; copy that file to
`report/data/extension_record.csv` when refreshing the report table source.
