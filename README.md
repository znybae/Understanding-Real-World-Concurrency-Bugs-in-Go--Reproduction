# CS340 Research Paper Replication: Topic 5

This repository contains the reproduction artifacts for the research paper:  
**"Understanding Real-World Concurrency Bugs in Go"** (*ASPLOS 2019*).

---

## 1. Project Directory Structure

```text
.
├── Dockerfile              # Unified runtime environment (Ubuntu 18.04 + Go 1.10.8)
├── .gitignore              # Git ignore rules for build artifacts and large files
├── .gitattributes          # Line-ending normalizations (LF enforcement)
├── README.md               # Quickstart and execution guide
├── scripts/                # Automated batch execution and test drivers
├── bugs/
│   ├── channel/            # Reproductions for Channel-related blocking bugs
│   └── shared_memory/     # Reproductions for Shared-memory & data race bugs
├── logs/
│   ├── channel/            # Raw logs from Channel reproduction runs
│   └── shared_memory/     # Raw logs from Shared-memory reproduction runs
├── analysis/               # Visualization scripts and generated comparison charts
├── extension/              # Extended experiments under modern Go environments
└── report/                 # LaTeX source files for the final report
```

---

## 2. Environment Setup

To ensure strict reproducibility and eliminate cross-platform variances between Windows and macOS, all experiments run inside an isolated Docker container pinned to **Go 1.10.8 on Linux amd64**.

### Step 1: Build the Docker Image
From the repository root, execute:
```bash
docker build --platform linux/amd64 -t cs340-go-bugs .
```

### Step 2: Run the Docker Container
Launch the container with the project workspace mounted:

* **On macOS / Linux:**
  ```bash
  docker run --rm -it -v $(pwd):/workspace cs340-go-bugs
  ```

* **On Windows (PowerShell):**
  ```powershell
  docker run --rm -it -v ${PWD}:/workspace cs340-go-bugs
  ```

---

## 3. Verified Environment Specs
* **Base OS**: Ubuntu 18.04 LTS (x86_64)
* **Go Version**: `go1.10.8 linux/amd64`
* **Target Architecture**: `linux/amd64`