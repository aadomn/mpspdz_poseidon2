# Dockerfile for "Towards Practical Multi-Party Hash Chains using AO Primitives - With Applications to Threshold Hash-Based Signatures" experiments
# Based on Ubuntu 24.04 with MP-SPDZ framework

FROM ubuntu:24.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for MP-SPDZ
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    automake \
    cmake \
    clang \
    iproute2 \
    libboost-all-dev \
    libsodium-dev \
    libssl-dev \
    libtool \
    libgmp-dev \
    libmpfr-dev \
    libmpfr6 \
    m4 \
    texinfo \
    yasm \
    python3 \
    python3-dev \
    python3-pip \
    vim \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /root

# Clone MP-SPDZ (using a specific version for reproducibility)
# You can change the version as needed
ARG MPSPDZ_VERSION=v0.4.1
RUN git clone https://github.com/data61/MP-SPDZ.git && \
    cd MP-SPDZ && \
    git checkout ${MPSPDZ_VERSION} && \
    echo 'MY_CFLAGS += -DN_MAMA_MACS=2' >> CONFIG && \
    make -j$(nproc)

# Generate players' key and certificate
RUN cd MP-SPDZ && \
    Scripts/setup-ssl.sh

# Set MP-SPDZ as the working directory
WORKDIR /root/MP-SPDZ

# Copy programs and scripts
COPY programs/*.mpc /root/MP-SPDZ/Programs/Source/
COPY programs/poseidon2.py /root/MP-SPDZ/Compiler/
COPY scripts/ /root/scripts/

# Create results directory
RUN mkdir -p /root/results

# Default command
CMD ["/bin/bash"]