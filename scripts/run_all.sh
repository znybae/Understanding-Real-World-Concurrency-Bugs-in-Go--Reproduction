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
# run_case "shared_memory" "race_demo" "go test -race -v ./bugs/shared_memory/..."

echo ""
echo "=========================================="
echo " All reproduction runs completed."
echo " Check the logs/ directory for raw outputs."
echo "=========================================="