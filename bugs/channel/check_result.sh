#!/usr/bin/env bash
set -uo pipefail

case_name="${1:?case_name required}"
shift

tmp_out=$(mktemp)
trap 'rm -f "$tmp_out"' EXIT

"$@" >"$tmp_out" 2>&1
status=$?

cat "$tmp_out"
printf 'COMMAND_EXIT_CODE=%s\n' "$status"

case "$case_name" in
    docker_24007_buggy)
        if (( status != 0 )) && grep -Fq "panic: close of closed channel" "$tmp_out"; then
            echo "RESULT=EXPECTED_PANIC"
            exit 0
        fi
        ;;
    k8s_5316_buggy)
        if (( status != 0 )) && grep -Fq "test timed out after 5s" "$tmp_out" && grep -Fq "[chan send]" "$tmp_out"; then
            echo "RESULT=EXPECTED_BLOCKING"
            exit 0
        fi
        ;;
    *)
        echo "RESULT=UNKNOWN_CASE"
        exit 2
        ;;
esac

echo "RESULT=UNEXPECTED_OUTCOME"
exit 1