ARG BASE_IMAGE=ubuntu:20.04

FROM $BASE_IMAGE as builder
SHELL ["/bin/bash", "-c"]

ARG NODES
ARG WALLET_SS58_ADDRESS
ENV WALLET_SS58_ADDRESS=$WALLET_SS58_ADDRESS

# LABEL ai.opentensor.image.authors="sepehr@opentensor.ai" \
#         ai.opentensor.image.vendor="Opentensor Foundation" \
#         ai.opentensor.image.title="opentensor/subtensor" \
#         ai.opentensor.image.description="Opentensor Subtensor Blockchain" \
#         ai.opentensor.image.revision="${VCS_REF}" \
#         ai.opentensor.image.created="${BUILD_DATE}" \
#         ai.opentensor.image.documentation="https://docs.bittensor.com"

ENV RUST_BACKTRACE 1

RUN apt update && \
    apt install -y make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler tmux && \ 
    rm -rf /var/lib/apt/lists/*

RUN set -o pipefail && curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN git clone https://github.com/opentensor/subtensor.git
WORKDIR /subtensor

RUN echo "FEATURES='pow-faucet runtime-benchmarks' BT_DEFAULT_TOKEN_WALLET=$WALLET_SS58_ADDRESS bash scripts/localnet.sh" >> setup_and_run.sh
RUN chmod +x setup_and_run.sh && \
    ./setup_and_run.sh


# RUN export BT_MINER_TOKEN_WALLET=$(cat ~/.bittensor/wallets/miner/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') \
#     export BT_VALIDATOR_TOKEN_WALLET=$(cat ~/.bittensor/wallets/validator/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') \

#     btcli wallet transfer --subtensor.network ws://127.0.0.1:9946 --wallet.name $wallet --dest $BT_MINER_TOKEN_WALLET --amount 1000 --no_prompt \
#     btcli wallet transfer --subtensor.network ws://127.0.0.1:9946 --wallet.name $wallet --dest $BT_VALIDATOR_TOKEN_WALLET --amount 10000 --no_prompt

#     # Register wallet hotkeys to subnet
#     btcli subnet register --wallet.name miner --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
#     btcli subnet register --wallet.name validator --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

#     # Add stake to the validator
#     btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --amount 10000 --no_prompt

#     # Ensure both the miner and validator keys are successfully registered.
#     btcli subnet list --subtensor.chain_endpoint ws://127.0.0.1:9946
#     btcli wallet overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
#     btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

CMD tail -f /dev/null