# Build container
FROM debian:11-slim AS builder

# Build arguments
ARG BRANCH=main

# install tools and dependencies
RUN apt update && \
  apt upgrade -y && \
  apt install -y python3 python3-pip gcc python3-dev cargo git g++ cmake make curl && \
  git clone -b $BRANCH https://github.com/gitphantomman/scraping_subnet.git app && \
  cd app && \
  pip3 install -r requirements.txt && \
  pip3 install -e . && \
  apt purge -y gcc python3-dev cargo git g++ cmake make curl && \
  apt -y autoremove && \
  rm -rf /var/lib/apt/lists/*

# Start inside the bittensor git folder
WORKDIR /app