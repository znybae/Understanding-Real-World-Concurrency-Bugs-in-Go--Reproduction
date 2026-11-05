#!/usr/bin/env bash
set -uo pipefail

echo "=========================================="
echo " Starting CS340 Bug Reproduction Suite"
echo " Environment: Go $(go version 2>/dev/null || echo 'Unknown')"
echo " Timestamp:   $(date)"
echo "=========================================="

# 确保输出目录完整
mkdir -p logs/channel logs/shared_memory

# 测试用例执行与日志归档函数
run_case() {
    local category="$1"
    local case_name="$2"
    local run_cmd="$3"
    local log_file="logs/${category}/${case_name}.log"

    echo -n "[RUNNING] [${category}] ${case_name} ... "
    
    if eval "${run_cmd}" > "${log_file}" 2>&1; then
        echo "PASS (Log: ${log_file})"
    else
        echo "FAIL/TRIGGERED (Log: ${log_file})"
    fi
}

echo ""
echo "=== 1. Channel Bug Suite ==="
# 预留执行位，后续添加具体用例在此取消注释调用
# run_case "channel" "blocking_demo" "go test -v ./bugs/channel/..."

echo ""
echo "=== 2. Shared Memory Bug Suite ==="
# 预留执行位，支持启用 -race 竞态检测器
run_case "shared_memory" "docker_25384_buggy" "bash bugs/shared_memory/check_result.sh docker_25384_buggy timeout 120s go test -race -v -count=1 -timeout=5s ./bugs/shared_memory/waitgroup_deadlock"
run_case "shared_memory" "docker_25384_fixed" "bash bugs/shared_memory/check_result.sh docker_25384_fixed timeout 120s go test -race -v -count=1 -timeout=5s ./bugs/shared_memory/waitgroup_deadlock/fixed"
run_case "shared_memory" "docker_27037_buggy" "bash bugs/shared_memory/check_result.sh docker_27037_buggy timeout 120s go test -race -v -count=1 -timeout=10s ./bugs/shared_memory/docker_race"
run_case "shared_memory" "docker_27037_fixed" "bash bugs/shared_memory/check_result.sh docker_27037_fixed timeout 120s go test -race -v -count=1 -timeout=10s ./bugs/shared_memory/docker_race/fixed"

echo ""
echo "=========================================="
echo " All reproduction runs completed."
echo " Check the logs/ directory for raw outputs."
echo "=========================================="