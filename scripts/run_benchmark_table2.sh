#!/bin/bash

source "$(dirname "$0")/benchmark_common.sh"

PROGRAM_NAME="poseidon2_chains"
CHAIN_LENGTHS=(8 128 512)

trap cleanup_network EXIT INT TERM

run_benchmark_suite "${PROGRAM_NAME}" "${CHAIN_LENGTHS[@]}"

python3 scripts/parse_logs.py /root/results --prefix poseidon2_chains --output results/table2.txt

cat results/table2.txt
