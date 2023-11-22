# Update your system packages
sudo apt update 

# Install additional required libraries and tools
sudo apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler

# Install rust and cargo
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Update your shell's source to include Cargo's path
source "$HOME/.cargo/env"

# Clone subtensor and enter the directory
cd ../
git clone https://github.com/opentensor/subtensor.git
cd subtensor

# Update to the nightly version of rust
./scripts/init.sh

# Initialize your local subtensor chain in development mode. This command will set up and run a local subtensor network.
# Run this in the background (or send to tmux/forked shell?)

# Check if inside a tmux session
# Start a new tmux session and create a new pane, but do not switch to it
tmux new-session -d -s localnet -n 'script' 'bash ./scripts/localnet.sh'
# Notify the user
echo "localnet.sh is running in a detached tmux session named 'localnet'"
echo "You can attach to this session with: tmux attach-session -t localnet"


# Navigate to your project directory
cd ../bittensor-subnet-template

# Install the bittensor-subnet-template python package
python -m pip install -e .

# Create a coldkey for the owner role
btcli wallet new_coldkey --wallet.name owner2

# Set up the miner's wallets
btcli wallet new_coldkey --wallet.name miner2
btcli wallet new_hotkey --wallet.name miner2 --wallet.hotkey default

# Set up the validator's wallets
btcli wallet new_coldkey --wallet.name validator2
btcli wallet new_hotkey --wallet.name validator2 --wallet.hotkey default

# Get yourself some test tao
btcli wallet faucet --wallet.name owner2 --subtensor.chain_endpoint ws://127.0.0.1:9946 
btcli wallet faucet --wallet.name validator2 --subtensor.chain_endpoint ws://127.0.0.1:9946 

# Register a subnet
btcli subnet recycle_register --wallet.name miner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946

# Add stake to the validator
btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946

# Ensure both the miner and validator keys are successfully registered.
btcli subnet list --subtensor.chain_endpoint ws://127.0.0.1:9946
btcli wallet overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946
btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946

# TODO: Send to tmux and open a 2-pane window
python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug
python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug

# Check if inside a tmux session
if [ -z "$TMUX" ]; then
    # Start a new tmux session and run the miner in the first pane
    tmux new-session -d -s bittensor -n 'miner' 'python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug'
    
    # Split the window and run the validator in the new pane
    tmux split-window -h -t bittensor:miner 'python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug'
    
    # Attach to the new tmux session
    tmux attach-session -t bittensor
else
    # If already in a tmux session, create two panes in the current window
    tmux split-window -h 'python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug'
    tmux split-window -v -t 0 'python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug'
fi
