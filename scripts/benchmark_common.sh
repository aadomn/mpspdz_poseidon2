#!/bin/bash
# Common functions for MP-SPDZ benchmark scripts

set -e

# Common configuration
NUM_PARTIES=3
KOALABEAR=2130706433
LOG_KOALABEAR=31
NETWORK_DELAYS=(1 10 100)
THROUGHPUT="1000Mbps"
PROTOCOLS=(mama mascot atlas mal-shamir)
RESULTS_DIR="/root/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to set up network delay using tc
setup_network() {
    local delay=$1
    echo "Setting up network: delay=${delay}ms, throughput=${THROUGHPUT}"

    tc qdisc add dev lo root netem delay ${delay}ms rate ${THROUGHPUT} 2>/dev/null || {
        echo "Warning: Failed to set up network delay. tc qdisc might already exist."
        echo "Cleaning up and retrying..."
        tc qdisc del dev lo root 2>/dev/null || true
        tc qdisc add dev lo root netem delay ${delay}ms rate ${THROUGHPUT}
    }

    return 0
}

# Function to remove network delay
cleanup_network() {
    echo "Cleaning up network settings..."

    if [ "$EUID" -eq 0 ]; then
        sudo tc qdisc del dev lo root 2>/dev/null || {
            echo "No network delay to clean up."
        }
    fi
}

# Function to compile and return the generated program name
compile_program() {
    local program_name=$1
    shift
    local params="$@"
        
    # Compile and capture output to find the generated program name
    local compile_output=$(./compile.py ${program_name} ${params} -F ${LOG_KOALABEAR} 2>&1 | tee /dev/tty)
    
    # Extract the compiled program name from compiler output
    local compiled_name=$(echo "$compile_output" | grep -oP "Writing to Programs/Schedules/\K[^/\s]+(?=\.sch)" | head -1)
    
    echo "$compiled_name"
}

# Function to run a single experiment
run_single_experiment() {
    local protocol=$1
    local delay=$2
    local network_enabled=$3
    local compiled_program_name=$4  # This is now the actual compiled name

    local delay_label="${delay}ms"
    if [ "$network_enabled" = false ]; then
        delay_label="no_delay"
    fi

    echo "=========================================="
    echo "Running experiment:"
    echo "  Program: ${compiled_program_name}"
    echo "  Protocol: ${protocol}"
    echo "  Network delay: ${delay_label}"
    echo "  Throughput: ${THROUGHPUT}"
    echo "=========================================="

    local output_file="${RESULTS_DIR}/${compiled_program_name}_${protocol}_${delay_label}_${TIMESTAMP}.log"

    echo "Executing: ./Scripts/${protocol}.sh ${compiled_program_name}"

    if [ "$protocol" = "atlas" ] || [ "$protocol" = "mama" ]; then
        ./Scripts/${protocol}.sh ${compiled_program_name} -N ${NUM_PARTIES} -P ${KOALABEAR} -v 2>&1 | tee "${output_file}"
    else
        ./Scripts/${protocol}.sh ${compiled_program_name} -N ${NUM_PARTIES} -P ${KOALABEAR} -S ${LOG_KOALABEAR} -v 2>&1 | tee "${output_file}"
    fi

    echo "Results saved to: ${output_file}"
    echo ""
}

# Function to run benchmark suite
run_benchmark_suite() {
    local program_name=$1
    shift
    local params_array=("$@")

    echo "======================================"
    echo "MP-SPDZ Benchmark Suite"
    echo "======================================"
    echo "Program: ${program_name}"
    echo "Protocols: ${PROTOCOLS[*]}"
    echo "Network delays: ${NETWORK_DELAYS[*]}ms"
    echo "Throughput: ${THROUGHPUT}"
    echo "Timestamp: ${TIMESTAMP}"
    echo "======================================"
    echo ""

    for params in "${params_array[@]}"; do
        # Compile and get the actual compiled program name
        echo "Compiling ${program_name}.mpc with parameters: ${params}..."
        compiled_name=$(compile_program "${program_name}" ${params})
        echo ""

        for protocol in "${PROTOCOLS[@]}"; do
            for delay in "${NETWORK_DELAYS[@]}"; do
                network_enabled=false
                if setup_network ${delay}; then
                    network_enabled=true
                fi

                # Pass the compiled name, not the original source name
                run_single_experiment "${protocol}" "${delay}" "${network_enabled}" "${compiled_name}"

                if [ "$network_enabled" = true ]; then
                    cleanup_network
                fi

                sleep 2
            done
        done
    done

    echo "======================================"
    echo "All experiments complete!"
    echo "Results are saved in: ${RESULTS_DIR}"
    echo "======================================"
    echo ""
    echo "Result files:"
    ls -lh ${RESULTS_DIR}/*${TIMESTAMP}.log 2>/dev/null || echo "No result files found."
}