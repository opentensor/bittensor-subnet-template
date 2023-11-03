# Use debian:11-slim as the base image
FROM debian:11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt
RUN pip3 install -e .
