#!/usr/bin/env bash
# Run the Week 3 modern-Go comparison (configs A, B, C).
#
# From the repository root on the host:
#   bash extension/run_extension.sh
#   REPEATS=10 bash extension/run_extension.sh
#
# The host driver launches the official baseline image (config A, Go 1.10.8)
# and the modern image (configs B and C, Go 1.23.12) with a bind mount.
# Inside a container this script is re-invoked as:
#   bash extension/run_extension.sh --inside
#
# It copies bug sources into extension/workspace/ (it never edits bugs/),
# writes go.mod only for B and C, runs every case N times, and records raw
# logs plus summaries under extension/results/.
set -uo pipefail

repeats=${REPEATS:-10}
if ! [[ "$repeats" =~ ^[1-9][0-9]*$ ]] || (( repeats > 1000 )); then
    echo "REPEATS must be an integer from 1 to 1000" >&2
    exit 2
fi

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)

export LC_ALL=C
export GORACE="${GORACE:-exitcode=66}"
export GOTOOLCHAIN="${GOTOOLCHAIN:-local}"
export GOPROXY="${GOPROXY:-off}"
export GOSUMDB="${GOSUMDB:-off}"
export CGO_ENABLED="${CGO_ENABLED:-1}"

cases=(
    "channel|docker_24007_buggy|./channel|TestDocker24007|10s|no|Figure 10|Block 2|non-blocking / message passing|buggy|EXPECTED_PANIC"
    "channel|k8s_5316_buggy|./channel|TestK8s5316|5s|no|Figure 1|Block 2|blocking / message passing|buggy|EXPECTED_BLOCKING"
    "shared_memory|docker_25384_buggy|./waitgroup_deadlock|TestWaitGroupDeadlock|5s|yes|Figure 5|Block 3|blocking / shared memory|buggy|EXPECTED_BLOCKING"
    "shared_memory|docker_25384_fixed|./waitgroup_deadlock/fixed|TestWaitGroupFixed|5s|yes|Figure 5|Block 3|blocking / shared memory|fixed|FIXED_PASS"
    "shared_memory|docker_27037_buggy|./docker_race|TestDockerRace|10s|yes|Figure 8|Block 3|non-blocking / shared memory|buggy|EXPECTED_RACE"
    "shared_memory|docker_27037_fixed|./docker_race/fixed|TestDockerRaceFixed|10s|yes|Figure 8|Block 3|non-blocking / shared memory|fixed|FIXED_PASS"
)

prepare_workspace() {
    local dest="$repo_root/extension/workspace"
    rm -rf "$dest"
    mkdir -p "$dest/channel" "$dest/docker_race/fixed" "$dest/waitgroup_deadlock/fixed" || return 1
    cp "$repo_root/bugs/channel/docker_24007_test.go" \
       "$repo_root/bugs/channel/k8s_5316_test.go" \
       "$dest/channel/" || return 1
    cp "$repo_root/bugs/shared_memory/docker_race/docker_27037_test.go" \
       "$repo_root/bugs/shared_memory/docker_race/docker_race.go" \
       "$dest/docker_race/" || return 1
    cp "$repo_root/bugs/shared_memory/docker_race/fixed/docker_27037_test.go" \
       "$repo_root/bugs/shared_memory/docker_race/fixed/main.go" \
       "$dest/docker_race/fixed/" || return 1
    cp "$repo_root/bugs/shared_memory/waitgroup_deadlock/docker_25384_test.go" \
       "$repo_root/bugs/shared_memory/waitgroup_deadlock/waitgroup_deadlock.go" \
       "$dest/waitgroup_deadlock/" || return 1
    cp "$repo_root/bugs/shared_memory/waitgroup_deadlock/fixed/docker_25384_test.go" \
       "$repo_root/bugs/shared_memory/waitgroup_deadlock/fixed/main.go" \
       "$dest/waitgroup_deadlock/fixed/" || return 1
}

write_go_mod() {
    local lang="$1"
    local dest="$repo_root/extension/workspace/go.mod"
    if [[ -z "$lang" ]]; then
        rm -f "$dest"
        return 0
    fi
    printf 'module cs340/extension\n\ngo %s\n' "$lang" > "$dest"
}

record_config_environment() {
    local cfg_dir="$1"
    mkdir -p "$cfg_dir"
    {
        date -u
        go version
        go env GOOS GOARCH CGO_ENABLED CC GOTOOLCHAIN GOPROXY GOSUMDB GOMAXPROCS GOPATH GOROOT
        go env
        gcc --version
        cat /etc/os-release
        uname -a
        printf 'CONFIG=%s\n' "${CONFIG}"
        printf 'LANGUAGE_VERSION=%s\n' "${LANGUAGE_VERSION}"
        printf 'REPEATS=%s\n' "$repeats"
        printf 'GORACE=%s\n' "$GORACE"
        printf 'GOMAXPROCS=%s\n' "${GOMAXPROCS:-unset}"
        printf 'AVAILABLE_PROCESSORS='
        nproc
        printf 'CGO_ENABLED_ENV=%s\n' "$(go env CGO_ENABLED)"
        if [[ -f "$repo_root/extension/workspace/go.mod" ]]; then
            echo '----- go.mod -----'
            cat "$repo_root/extension/workspace/go.mod"
            echo '----- go list -----'
            (cd "$repo_root/extension/workspace" && go list -m -f '{{.Path}} {{.GoVersion}}')
            (cd "$repo_root/extension/workspace" && go list -f '{{.ImportPath}} module_go={{.Module.GoVersion}} dir={{.Dir}}' ./channel ./docker_race ./docker_race/fixed ./waitgroup_deadlock ./waitgroup_deadlock/fixed)
        else
            echo 'go.mod: absent (GOPATH mode)'
            ls -la "$repo_root/extension/workspace"
        fi
        printf 'GO_BINARY_SHA256='
        sha256sum "$(command -v go)"
        if [[ -f /usr/local/go/VERSION ]]; then
            printf 'GO_DISTRIBUTION_VERSION='
            cat /usr/local/go/VERSION
            printf '\n'
        fi
    } > "$cfg_dir/environment.txt" 2>&1
}

run_inside() {
    local config="${CONFIG:?CONFIG is required inside the container}"
    local run_dir="${RUN_DIR:?RUN_DIR is required inside the container}"
    if [[ "$run_dir" != /* ]]; then
        run_dir="$repo_root/$run_dir"
    fi
    local cfg_dir="$run_dir/$config"
    local language_version=""
    local go_version_expected=""

    case "$config" in
        A)
            language_version="gopath"
            go_version_expected="go version go1.10.8 linux/amd64"
            write_go_mod ""
            ;;
        B)
            language_version="1.21"
            go_version_expected="go version go1.23.12 linux/amd64"
            write_go_mod "1.21"
            ;;
        C)
            language_version="1.22"
            go_version_expected="go version go1.23.12 linux/amd64"
            write_go_mod "1.22"
            ;;
        *)
            echo "Unknown CONFIG=$config" >&2
            exit 2
            ;;
    esac
    CONFIG="$config"
    LANGUAGE_VERSION="$language_version"

    for tool in go gcc timeout sha256sum; do
        command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
    done
    if [[ "$(go version)" != "$go_version_expected" ]]; then
        echo "Unexpected toolchain: $(go version) (want $go_version_expected)" >&2
        exit 2
    fi
    if [[ "$(go env CGO_ENABLED)" != 1 ]]; then
        echo "CGO_ENABLED must be 1" >&2
        exit 2
    fi
    if [[ "$config" != A && "$(go env GOTOOLCHAIN)" != local ]]; then
        echo "GOTOOLCHAIN must be local for configs B/C to avoid auto-downloads" >&2
        exit 2
    fi

    record_config_environment "$cfg_dir"

    mkdir -p "$cfg_dir"
    local summary="$run_dir/summary.tsv"
    if [[ ! -f "$summary" ]]; then
        printf 'iteration\tconfig\tlanguage_version\tgo_version\tcase\tcommand_exit_code\tchecker_exit_code\tresult\tduration_s\trace_report\tdeadlock_report\tversions\tlog\n' > "$summary"
    fi

    local go_ver
    go_ver=$(go version | awk '{print $3}')

    run_case() {
        local iteration="$1" suite="$2" case_name="$3" package="$4" test_name="$5" limit="$6" use_race="$7"
        local log_file="$cfg_dir/${case_name}_${iteration}.log"
        local -a cmd
        if [[ "$use_race" == yes ]]; then
            cmd=(timeout 120s go test -race -v -count=1 "-timeout=$limit" -run "^${test_name}$" "$package")
        else
            cmd=(timeout 120s go test -v -count=1 "-timeout=$limit" -run "^${test_name}$" "$package")
        fi
        local start end duration checker_status result command_status race_report deadlock_report versions
        start=$(date +%s.%N)
        {
            printf 'CONFIG=%s\nLANGUAGE_VERSION=%s\nGO_VERSION=%s\n' "$config" "$language_version" "$(go version)"
            printf 'WORKDIR=%s\n' "$repo_root/extension/workspace"
            if [[ -f "$repo_root/extension/workspace/go.mod" ]]; then
                echo 'GOMOD='
                cat "$repo_root/extension/workspace/go.mod"
            else
                echo 'GOMOD=absent'
            fi
            printf 'COMMAND='
            printf '%q ' "${cmd[@]}"
            printf '\n'
            bash "$repo_root/bugs/${suite}/check_result.sh" "$case_name" "${cmd[@]}"
        } > "$log_file" 2>&1
        checker_status=$?
        end=$(date +%s.%N)
        duration=$(python3 -c "print('{:.3f}'.format(float('$end') - float('$start')))")
        result=$(sed -n 's/^RESULT=//p' "$log_file" | tail -n 1)
        command_status=$(sed -n 's/^COMMAND_EXIT_CODE=//p' "$log_file" | tail -n 1)
        result=${result:-CHECKER_ERROR}
        command_status=${command_status:-NA}
        if grep -Fq 'WARNING: DATA RACE' "$log_file"; then
            race_report=yes
        else
            race_report=no
        fi
        if grep -Fq 'all goroutines are asleep - deadlock' "$log_file"; then
            deadlock_report=yes
        else
            deadlock_report=no
        fi
        versions=$(grep -E '^v1\.[0-9]+$' "$log_file" | paste -sd',' -)
        versions=${versions:-}
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$iteration" "$config" "$language_version" "$go_ver" "$case_name" \
            "$command_status" "$checker_status" "$result" "$duration" \
            "$race_report" "$deadlock_report" "$versions" "$log_file" >> "$summary"
        printf '[%s/%s] [%s/%s] %s: %s (exit=%s checker=%s race=%s deadlock=%s duration=%ss versions=%s)\n' \
            "$iteration" "$repeats" "$config" "$language_version" "$case_name" \
            "$result" "$command_status" "$checker_status" "$race_report" "$deadlock_report" \
            "$duration" "$versions"
    }

    local iter entry suite case_name package test_name limit use_race rest
    for ((iter=1; iter<=repeats; iter++)); do
        for entry in "${cases[@]}"; do
            IFS='|' read -r suite case_name package test_name limit use_race rest <<<"$entry"
            (cd "$repo_root/extension/workspace" && run_case "$iter" "$suite" "$case_name" "$package" "$test_name" "$limit" "$use_race")
        done
    done
}

run_host() {
    cd "$repo_root" || exit 2
    for tool in docker python3 sha256sum git; do
        command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
    done

    local base_image=${BASE_IMAGE:-cs340-go-bugs}
    local modern_image=${MODERN_IMAGE:-cs340-go-bugs-modern}

    if ! docker image inspect "$base_image" >/dev/null 2>&1; then
        echo "Missing image $base_image. Build it with:" >&2
        echo "  docker build --platform linux/amd64 -t $base_image ." >&2
        exit 2
    fi
    if ! docker image inspect "$modern_image" >/dev/null 2>&1; then
        echo "Missing image $modern_image. Build it with:" >&2
        echo "  docker build --platform linux/amd64 -f extension/Dockerfile.modern -t $modern_image extension/" >&2
        exit 2
    fi

    mkdir -p "$repo_root/extension/results" || exit 2
    local run_dir
    run_dir=$(mktemp -d "$repo_root/extension/results/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 2
    local rel_run_dir
    rel_run_dir=$(python3 -c "import os; print(os.path.relpath('$run_dir', '$repo_root'))")
    printf 'Evidence directory: %s\n' "$rel_run_dir"

    prepare_workspace || { echo "Failed to copy bug sources" >&2; exit 2; }

    {
        echo "===== Host ====="
        date -u
        date
        printf 'HOST_UNAME='
        uname -a
        if [[ -f /etc/os-release ]]; then
            cat /etc/os-release
        fi
        printf 'HOST_NPROC='
        nproc
        printf 'DOCKER_VERSION='
        docker version --format '{{.Server.Version}}' 2>/dev/null || docker version
        echo "BASE_IMAGE=$base_image"
        echo "MODERN_IMAGE=$modern_image"
        echo "REPEATS=$repeats"
        echo "GORACE=$GORACE"
        echo "GOMAXPROCS=${GOMAXPROCS:-unset}"
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            printf 'COMMIT='
            git rev-parse HEAD
            echo 'WORKTREE_STATUS:'
            git status --short --untracked-files=normal
        else
            echo 'COMMIT=unavailable'
        fi
        echo "===== Baseline image ====="
        docker image inspect "$base_image" --format 'Id={{.Id}} Created={{.Created}} Size={{.Size}} Architecture={{.Architecture}} Os={{.Os}}'
        echo "===== Modern image ====="
        docker image inspect "$modern_image" --format 'Id={{.Id}} Created={{.Created}} Size={{.Size}} Architecture={{.Architecture}} Os={{.Os}}'
        echo "===== Dockerfiles ====="
        sha256sum "$repo_root/Dockerfile" "$repo_root/extension/Dockerfile.modern" "$repo_root/extension/run_extension.sh" "$repo_root/extension/summarize_extension.py"
        echo "Pinned modern toolchain: go1.23.12 linux-amd64"
        echo "Official tarball: https://go.dev/dl/go1.23.12.linux-amd64.tar.gz"
        echo "Official SHA256: d3847fef834e9db11bf64e3fb34db9c04db14e068eeb064f49af747010454f90"
    } > "$run_dir/environment.txt" 2>&1

    {
        echo "# Original bug sources"
        find "$repo_root/bugs" -type f \( -name '*.go' -o -name '*.sh' \) -print0 | sort -z | xargs -0 sha256sum
        echo "# Copied workspace sources"
        find "$repo_root/extension/workspace" -type f -print0 | sort -z | xargs -0 sha256sum
        echo "# Scripts and Dockerfiles"
        sha256sum "$repo_root/Dockerfile" \
                  "$repo_root/extension/Dockerfile.modern" \
                  "$repo_root/extension/run_extension.sh" \
                  "$repo_root/extension/summarize_extension.py" \
                  "$repo_root/bugs/channel/check_result.sh" \
                  "$repo_root/bugs/shared_memory/check_result.sh"
    } > "$run_dir/input_sha256.txt"

    # Confirm the copies match the files under bugs/.
    python3 - << PY
import hashlib, pathlib, sys
root = pathlib.Path("$repo_root")
pairs = [
    ("bugs/channel/docker_24007_test.go", "extension/workspace/channel/docker_24007_test.go"),
    ("bugs/channel/k8s_5316_test.go", "extension/workspace/channel/k8s_5316_test.go"),
    ("bugs/shared_memory/docker_race/docker_27037_test.go", "extension/workspace/docker_race/docker_27037_test.go"),
    ("bugs/shared_memory/docker_race/docker_race.go", "extension/workspace/docker_race/docker_race.go"),
    ("bugs/shared_memory/docker_race/fixed/docker_27037_test.go", "extension/workspace/docker_race/fixed/docker_27037_test.go"),
    ("bugs/shared_memory/docker_race/fixed/main.go", "extension/workspace/docker_race/fixed/main.go"),
    ("bugs/shared_memory/waitgroup_deadlock/docker_25384_test.go", "extension/workspace/waitgroup_deadlock/docker_25384_test.go"),
    ("bugs/shared_memory/waitgroup_deadlock/waitgroup_deadlock.go", "extension/workspace/waitgroup_deadlock/waitgroup_deadlock.go"),
    ("bugs/shared_memory/waitgroup_deadlock/fixed/docker_25384_test.go", "extension/workspace/waitgroup_deadlock/fixed/docker_25384_test.go"),
    ("bugs/shared_memory/waitgroup_deadlock/fixed/main.go", "extension/workspace/waitgroup_deadlock/fixed/main.go"),
]
ok = True
for a, b in pairs:
    ha = hashlib.sha256((root/a).read_bytes()).hexdigest()
    hb = hashlib.sha256((root/b).read_bytes()).hexdigest()
    if ha != hb:
        print("COPY MISMATCH", a, b, file=sys.stderr)
        ok = False
if not ok:
    sys.exit(1)
print("All workspace copies match bugs/ sources.")
PY
    if (( $? != 0 )); then
        echo "Refusing to run with modified copies" >&2
        exit 2
    fi

    run_config() {
        local config="$1" image="$2"
        echo "===== Starting config $config on $image ====="
        docker run --rm --platform linux/amd64 \
            -v "$repo_root:/workspace" -w /workspace \
            -e CONFIG="$config" \
            -e REPEATS="$repeats" \
            -e RUN_DIR="$rel_run_dir" \
            -e GORACE="$GORACE" \
            -e GOTOOLCHAIN=local \
            -e GOPROXY=off \
            -e GOSUMDB=off \
            -e CGO_ENABLED=1 \
            -e LC_ALL=C \
            "$image" \
            bash /workspace/extension/run_extension.sh --inside
        local status=$?
        if (( status != 0 )); then
            echo "Config $config failed with status $status" >&2
            return "$status"
        fi
        return 0
    }

    run_config A "$base_image" || exit $?
    run_config B "$modern_image" || exit $?
    run_config C "$modern_image" || exit $?

    python3 "$repo_root/extension/summarize_extension.py" "$run_dir" || exit 2
    if command -v chown >/dev/null && [[ -n "${SUDO_USER:-}" || "$(id -u)" -eq 0 ]]; then
        chown -R --reference="$repo_root/extension/run_extension.sh" "$run_dir" "$repo_root/extension/workspace" 2>/dev/null || true
    fi
    # If files were created as root, try to make them user-writable.
    chmod -R a+rwX "$run_dir" "$repo_root/extension/workspace" 2>/dev/null || true
    printf 'Done. Evidence directory: %s\n' "$rel_run_dir"
    echo "$rel_run_dir" > "$repo_root/extension/results/LATEST"
}

if [[ "${1:-}" == "--inside" ]]; then
    run_inside
else
    run_host
fi
