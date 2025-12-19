#!/bin/bash

source "$(dirname "$0")/benchmark_common.sh"

PROGRAM_NAME="leansig"
LEANSIG_INSTANCES=(
    "48 10 326"
    "64 8 375"
    "68 4 114"
)

trap cleanup_network EXIT INT TERM

run_benchmark_suite "${PROGRAM_NAME}" "${LEANSIG_INSTANCES[@]}"

python3 /root/scripts/parse_logs.py /root/results --prefix leansig --output /root/results/table3.txt

cat /root/results/table3.txt
