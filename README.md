# CS340 Research Paper Replication: Topic 5

This repository contains the reproduction artifacts, automated test drivers, visualization scripts, and LaTeX report sources for the research paper:  
**"Understanding Real-World Concurrency Bugs in Go"** (*ASPLOS 2019*).

---

## 1. Project Directory Structure

```text
.
|-- Dockerfile                  # Unified runtime environment (Ubuntu 18.04 + Go 1.10.8)
|-- .gitignore                  # Git ignore rules for transient logs and large files
|-- .gitattributes              # Line-ending normalization (LF enforcement)
|-- README.md                   # Quickstart, environment setup, and execution guide
|-- scripts/                    # Automated multi-round batch runner & summary aggregator
|   |-- run_all.sh              # End-to-end 3-round test driver across all 6 test suites
|   `-- summarize_runs.py       # Log parser generating statistics.csv and summary.tsv
|-- bugs/
|   |-- channel/                # Channel blocking & double-close panic reproductions
|   |   |-- k8s_5316_test.go    # Figure 1: Unbuffered channel send timeout leak
|   |   |-- docker_24007_test.go# Figure 10: Concurrent double-close channel panic
|   |   `-- check_result.sh     # Automated symptom checker for channel cases
|   `-- shared_memory/          # Shared-memory data race & WaitGroup deadlock cases
|       |-- docker_race/        # Figure 8: Loop closure data race (buggy & fixed/)
|       |-- waitgroup_deadlock/ # Figure 5: WaitGroup.Wait() inside loop (buggy & fixed/)
|       `-- check_result.sh     # Automated symptom & -race checker
|-- analysis/                   # Python/Matplotlib scripts for paper vs. reproduction plots
|-- extension/                  # Extended experiments evaluating modern Go (Go 1.22+)
`-- report/                     # LaTeX report sources, tables, figures, and archived results
```

---

## 2. Environment Setup

To ensure strict reproducibility and eliminate cross-platform variances across Windows and macOS, all baseline experiments execute inside an isolated Docker container pinned to **Ubuntu 18.04 LTS + Go 1.10.8 (`linux/amd64`)** with `CGO_ENABLED=1` (required by Go's race detector).

### Step 1: Build the Docker Image
From the repository root, execute:
```bash
docker build --platform linux/amd64 -t cs340-go-bugs .
```

### Step 2: Launch an Interactive Container (Optional)
* **On macOS / Linux:**
  ```bash
  docker run --rm -it -v "$(pwd)":/workspace -w /workspace cs340-go-bugs
  ```
* **On Windows (PowerShell):**
  ```powershell
  docker run --rm -it -v "${PWD}:/workspace" -w /workspace cs340-go-bugs
  ```

---

## 3. One-Command Automated Reproduction

You can run the full 3-round verification suite (6 test targets $\times$ 3 rounds = 18 total checks) directly from the repository root without entering an interactive shell:

* **On macOS / Linux:**
  ```bash
  docker run --rm --platform linux/amd64 -v "$(pwd)":/workspace -w /workspace -e REPEATS=3 cs340-go-bugs bash scripts/run_all.sh
  ```
* **On Windows (PowerShell):**
  ```powershell
  docker run --rm --platform linux/amd64 -v "${PWD}:/workspace" -w /workspace -e REPEATS=3 cs340-go-bugs bash scripts/run_all.sh
  ```

### Expected Runtime & Output
* **Expected Runtime:** ~35–50 seconds for 3 complete rounds (dominated by intentional 5-second timeout windows on blocking/deadlock cases `k8s_5316` and `docker_25384`).
* **Generated Artifacts (Local Only):** Raw logs and aggregated summary tables (`summary.tsv`, `statistics.csv`, `environment.txt`, `input_sha256.txt`) are written to `logs/full_suite/run-<timestamp>/` (excluded from Git tracking via `.gitignore`).
* **Expected Verification Verdict:** All 18/18 checks match their expected symptoms (`EXPECTED_BLOCKING`, `EXPECTED_PANIC`, `EXPECTED_RACE`, or `FIXED_PASS`) with **0 unexpected mismatches**, matching the archived official run under `report/results/week2_full_suite/`.

---

## 4. Verified Environment Specs
* **Base OS:** Ubuntu 18.04.6 LTS (Bionic Beaver)
* **Go Toolchain:** `go1.10.8 linux/amd64` (GOPATH mode, `CGO_ENABLED=1`)
* **C Compiler:** GCC 7.5.0 (for `-race` runtime support)
* **Target Architecture:** `linux/amd64`