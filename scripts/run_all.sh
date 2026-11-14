#!/usr/bin/env bash
# Run from any directory inside the pinned Linux amd64 image.
set -uo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root" || exit 2
repeats=${REPEATS:-1}
if ! [[ "$repeats" =~ ^[1-9][0-9]*$ ]] || (( repeats > 1000 )); then
    echo "REPEATS must be an integer from 1 to 1000" >&2
    exit 2
fi
for tool in go gcc timeout python3 sha256sum; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
done
if [[ "$(go version)" != "go version go1.10.8 linux/amd64" ]] ||
   [[ "$(go env CGO_ENABLED)" != 1 ]]; then
    echo "Use cs340-go-bugs: Go 1.10.8 linux/amd64 with cgo enabled" >&2
    exit 2
fi
export LC_ALL=C
export GORACE='exitcode=66'
# Never overwrite a previous evidence run.
mkdir -p logs/shared_memory || exit 2
run_dir=$(mktemp -d "logs/shared_memory/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 2
printf 'Evidence directory: %s\n' "$run_dir"
{
    date -u
    go version
    go env GOOS GOARCH CGO_ENABLED CC
    gcc --version
    cat /etc/os-release
    uname -a
    printf 'REPEATS=%s\nGOMAXPROCS=%s\nGORACE=%s\n' "$repeats" "${GOMAXPROCS:-unset}" "$GORACE"
    printf 'AVAILABLE_PROCESSORS='; nproc
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        printf 'COMMIT='; git rev-parse HEAD
        echo 'WORKTREE_STATUS:'; git status --short --untracked-files=normal
        echo 'Note: generated logs can make this status dirty; see input hashes.'
    else
        echo 'COMMIT=unavailable (ZIP checkout); input hashes identify executed files'
    fi
} > "$run_dir/environment.txt" 2>&1
find bugs/shared_memory -type f \( -name '*.go' -o -name '*.sh' \) -print0 |
    sort -z | xargs -0 sha256sum > "$run_dir/input_sha256.txt"
sha256sum scripts/run_all.sh scripts/summarize_runs.py Dockerfile >> "$run_dir/input_sha256.txt"
printf 'iteration\tcase\tcommand_exit_code\tchecker_exit_code\tresult\tlog\n' > "$run_dir/summary.tsv"
failures=0
run_case() {
    local iteration="$1" case_name="$2" package="$3" test_name="$4" limit="$5"
    local log_file="$run_dir/${case_name}_${iteration}.log" checker_status result command_status
    local -a cmd=(timeout 120s go test -race -v -count=1 "-timeout=$limit" -run "^${test_name}$" "$package")
    {
        printf 'COMMAND='; printf '%q ' "${cmd[@]}"; printf '\n'
        bash bugs/shared_memory/check_result.sh "$case_name" "${cmd[@]}"
    } > "$log_file" 2>&1
    checker_status=$?
    result=$(sed -n 's/^RESULT=//p' "$log_file" | tail -n 1)
    command_status=$(sed -n 's/^COMMAND_EXIT_CODE=//p' "$log_file" | tail -n 1)
    result=${result:-CHECKER_ERROR}
    command_status=${command_status:-NA}
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$iteration" "$case_name" "$command_status" "$checker_status" "$result" "$log_file" >> "$run_dir/summary.tsv"
    printf '[%s/%s] %s: %s (checker=%s)\n' "$iteration" "$repeats" "$case_name" "$result" "$checker_status"
    if (( checker_status != 0 )); then failures=$((failures + 1)); fi
}
echo 'Channel suite: SKIPPED (no registered cases in this snapshot)'
for ((iteration=1; iteration<=repeats; iteration++)); do
    run_case "$iteration" docker_25384_buggy ./bugs/shared_memory/waitgroup_deadlock TestWaitGroupDeadlock 5s
    run_case "$iteration" docker_25384_fixed ./bugs/shared_memory/waitgroup_deadlock/fixed TestWaitGroupFixed 5s
    run_case "$iteration" docker_27037_buggy ./bugs/shared_memory/docker_race TestDockerRace 10s
    run_case "$iteration" docker_27037_fixed ./bugs/shared_memory/docker_race/fixed TestDockerRaceFixed 10s
done
python3 scripts/summarize_runs.py "$run_dir/summary.tsv" || exit 2
printf 'Unexpected/not-reproduced checks: %s\n' "$failures"
if (( failures > 0 )); then exit 1; fi
exit 0
