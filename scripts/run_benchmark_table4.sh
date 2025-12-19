#!/bin/bash

source "$(dirname "$0")/benchmark_common.sh"

PROGRAM_NAME="leansig_prec"
PARAMETERS=(
    "68 4 1"
    "68 4 2"
    "68 4 4"
)

trap cleanup_network EXIT INT TERM

run_benchmark_suite "${PROGRAM_NAME}" "${PARAMETERS[@]}"

python3 scripts/parse_logs.py /root/results --prefix leansig_prec --output results/table4.txt

cat results/table4.txt
