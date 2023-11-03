# Build container
FROM debian:11-slim AS builder

# Build arguments
ARG BRANCH

# Install tools and dependencies and perform cleanup in one layer to reduce image size
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y python3 python3-pip gcc python3-dev cargo git g++ cmake make curl && \
    git clone -b ${BRANCH} https://github.com/blockchain-insights/blockchain-data-subnet.git app && \
    cd app && \
    pip3 install -r requirements.txt && \
    pip3 install -e . && \
    apt-get purge -y gcc python3-dev cargo git g++ cmake make curl && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Start inside the bittensor git folder
WORKDIR /app
