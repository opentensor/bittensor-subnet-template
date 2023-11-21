#!/bin/bash

# Install subnet template inside a conda env
conda create -n template python=3.9
conda activate template
pip install -e .

# Prompt user for input
echo "Please enter the netuid:"
read netuid

echo "Please enter the miner hotkey:"
read miner_hotkey

echo "Please enter the validator hotkey:"
read validator_hotkey

# Run a miner and validator using pm2
pm2 start ~/bittensor-subnet-template/neurons/miner.py      --interpreter ~/miniconda3/envs/template/bin/python --name miner -- --netuid $netuid --wallet.name default --wallet.hotkey $miner_hotkey     --subtensor.network test --logging.debug --wandb.off
pm2 start ~/bittensor-subnet-template/neurons/validator.py --interpreter ~/miniconda3/envs/template/bin/python --name valid -- --netuid $netuid --wallet.name default --wallet.hotkey $validator_hotkey --subtensor.network test --logging.debug --wandb.off
