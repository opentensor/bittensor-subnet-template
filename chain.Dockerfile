FROM rust:1.77-bullseye

ARG NODES
ARG WALLET
ENV WALLET=$WALLET

RUN apt update && \
    apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler tmux

RUN git clone https://github.com/opentensor/subtensor.git
WORKDIR /subtensor

RUN echo "FEATURES='pow-faucet runtime-benchmarks' BT_DEFAULT_TOKEN_WALLET=$(cat ~/.bittensor/wallets/$WALLET/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') bash scripts/localnet.sh" >> setup_and_run.sh
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