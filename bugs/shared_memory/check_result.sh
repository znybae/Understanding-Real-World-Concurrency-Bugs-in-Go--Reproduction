#!/usr/bin/env bash
set -uo pipefail

case_name="$1"
shift
result_file=$(mktemp)
trap 'rm -f "$result_file"' EXIT

"$@" > "$result_file" 2>&1
status=$?
cat "$result_file"
echo "COMMAND_EXIT_CODE=$status"

case "$case_name" in
    docker_25384_buggy)
        if [ "$status" -eq 1 ] &&
           grep -Fq 'panic: test timed out after 5s' "$result_file" &&
           grep -Fq 'sync.(*WaitGroup).Wait' "$result_file"; then
            echo "RESULT=EXPECTED_BLOCKING"
            exit 0
        fi
        ;;
    docker_27037_buggy)
        if [ "$status" -eq 1 ] &&
           grep -Fq 'WARNING: DATA RACE' "$result_file" &&
           grep -Fq 'docker_race.go:' "$result_file"; then
            echo "RESULT=EXPECTED_RACE"
            exit 0
        fi
        ;;
    docker_25384_fixed|docker_27037_fixed)
        if [ "$status" -eq 0 ] &&
           grep -qx 'PASS' "$result_file" &&
           ! grep -Fq 'WARNING: DATA RACE' "$result_file"; then
            echo "RESULT=FIXED_PASS"
            exit 0
        fi
        ;;
esac

echo "RESULT=UNEXPECTED_OR_NOT_REPRODUCED"
exit 1
