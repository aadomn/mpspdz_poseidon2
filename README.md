# Benchmark of Poseidon2 Chains over MPC with the MP-SPDZ framework

The repository contains software artifacts to reproduce the benchmark results reported in the paper "Towards Practical Multi-Party Hash Chains using Arithmetization-Oriented Primitives - With Applications to Threshold Hash-Based Signatures" published in IACR CiC 2025/4.

## Instructions

Build the docker image by running

```
docker-compose build
```

Once complete you can run one of the benchmarks whose results are reported in the paper by running

```
docker-compose run mpc-poseidon2 /root/scripts/run_benchmark_table{x}.sh
```

where `{x}` is expected to be `2`, `3` or `4` depending on the benchmark table you would like to reproduce.

