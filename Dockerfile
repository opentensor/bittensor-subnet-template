# Use debian:11-slim as the base image
FROM debian:11-slim AS builder

# Build argument for specifying the branch
ARG BRANCH

# Update system packages
RUN apt-get update && apt-get upgrade -y

# Install system dependencies
RUN apt-get install -y python3 python3-pip gcc python3-dev cargo git g++ cmake make curl

# Clone the specific branch from the repository
RUN git clone -b ${BRANCH} https://github.com/blockchain-insights/blockchain-data-subnet.git app

# Install Python dependencies
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN pip3 install -e .

# Remove build dependencies to reduce image size
RUN apt-get purge -y gcc python3-dev cargo git g++ cmake make curl
RUN apt-get -y autoremove
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Start inside the bittensor git folder
WORKDIR /app
