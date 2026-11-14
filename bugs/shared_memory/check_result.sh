#!/usr/bin/env bash
set -uo pipefail
if (( $# < 2 )); then
    echo 'Usage: check_result.sh CASE COMMAND [ARG ...]' >&2
    exit 2
fi
case_name="$1"
shift
result_file=$(mktemp) || exit 2
trap 'rm -f "$result_file"' EXIT
"$@" > "$result_file" 2>&1
status=$?
cat "$result_file"
echo "COMMAND_EXIT_CODE=$status"
case "$case_name" in
    docker_25384_buggy)
        if [[ "$status" == 1 ]] &&
           grep -Fq '=== RUN   TestWaitGroupDeadlock' "$result_file" &&
           grep -Fq 'panic: test timed out after 5s' "$result_file" &&
           grep -Fq 'sync.(*WaitGroup).Wait' "$result_file" &&
           grep -Fq 'waitgroup_deadlock.go:' "$result_file" &&
           grep -Fq 'Task 0 finished' "$result_file" &&
           ! grep -Fq 'Starting task 1' "$result_file"; then
            echo 'RESULT=EXPECTED_BLOCKING'; exit 0
        fi
        ;;
    docker_27037_buggy)
        if [[ "$status" == 1 ]] &&
           grep -Fq '=== RUN   TestDockerRace' "$result_file" &&
           grep -Fq 'WARNING: DATA RACE' "$result_file" &&
           grep -Fq 'docker_race.go:' "$result_file" &&
           grep -Fq 'Read at ' "$result_file" &&
           grep -Fq 'write at ' "$result_file"; then
            echo 'RESULT=EXPECTED_RACE'; exit 0
        fi
        ;;
    docker_25384_fixed)
        if [[ "$status" == 0 ]] && grep -qx 'PASS' "$result_file" &&
           grep -Fq -- '--- PASS: TestWaitGroupFixed' "$result_file" &&
           grep -qx 'All tasks completed' "$result_file" &&
           [[ $(grep -Ec '^Task [01] finished$' "$result_file") == 2 ]] &&
           ! grep -Fq 'WARNING: DATA RACE' "$result_file"; then
            echo 'RESULT=FIXED_PASS'; exit 0
        fi
        ;;
    docker_27037_fixed)
        if [[ "$status" == 0 ]] && grep -qx 'PASS' "$result_file" &&
           grep -Fq -- '--- PASS: TestDockerRaceFixed' "$result_file" &&
           [[ "$(grep '^v1\.' "$result_file" | LC_ALL=C sort)" == $'v1.17\nv1.18\nv1.19\nv1.20' ]] &&
           ! grep -Fq 'WARNING: DATA RACE' "$result_file"; then
            echo 'RESULT=FIXED_PASS'; exit 0
        fi
        ;;
    *) echo 'RESULT=UNKNOWN_CASE'; exit 2 ;;
esac
if [[ "$status" == 124 || "$status" == 137 ]]; then
    echo 'RESULT=OUTER_TIMEOUT'
else
    echo 'RESULT=UNEXPECTED_OR_NOT_REPRODUCED'
fi
exit 1
