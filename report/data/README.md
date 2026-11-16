# Test record and official Week 2 logs

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
The extension experiment uses the same columns with a different `go_version`.
