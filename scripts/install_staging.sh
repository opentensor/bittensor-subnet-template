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
if [ ! -d "subtensor" ]; then
    git clone https://github.com/opentensor/subtensor.git
fi
cd subtensor
git pull

# Update to the nightly version of rust
./scripts/init.sh

# Navigate to your project directory
cd ../bittensor-subnet-template

# Install the bittensor-subnet-template python package
python -m pip install -e .

# Create a coldkey for the owner role
btcli wallet new_coldkey --wallet.name owner --no_password

# Set up the miner's wallets
btcli wallet new_coldkey --wallet.name miner --no_password
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default

# Set up the validator's wallets
btcli wallet new_coldkey --wallet.name validator --no_password
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default


## Setup localnet
# Initialize your local subtensor chain in development mode. This command will set up and run a local subtensor network.
cd ../subtensor

# Start a new tmux session and create a new pane, but do not switch to it
echo "export BT_DEFAULT_TOKEN_WALLET=\$(cat ~/.bittensor/wallets/owner/coldkeypub.txt | grep -oP '\"ss58Address\": \"\K[^\"]+')" > setup_and_run.sh
echo "bash ./scripts/localnet.sh" >> setup_and_run.sh
chmod +x setup_and_run.sh
tmux new-session -d -s localnet -n 'localnet'
tmux send-keys -t localnet 'bash ../subtensor/setup_and_run.sh' C-m

# Notify the user
echo "localnet.sh is running in a detached tmux session named 'localnet'"
echo "You can attach to this session with: tmux attach-session -t localnet"

# Transfer tokens to miner and validator coldkeys
export BT_owner_TOKEN_WALLET=$(cat ~/.bittensor/wallets/owner/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+')
export BT_miner_TOKEN_WALLET=$(cat ~/.bittensor/wallets/miner/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+')
export BT_validator_TOKEN_WALLET=$(cat ~/.bittensor/wallets/validator/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+')

btcli wallet transfer --subtensor.network ws://127.0.0.1:9946 --wallet.name owner --dest $BT_miner_TOKEN_WALLET --amount 1000 --no_prompt
btcli wallet transfer --subtensor.network ws://127.0.0.1:9946 --wallet.name owner --dest $BT_validator_TOKEN_WALLET --amount 1000 --no_prompt

# Register a subnet
btcli subnet create --wallet.name owner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

# Register wallet hotkeys to subnet
btcli subnet register --wallet.name miner --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
btcli subnet register --wallet.name validator --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

# Add stake to the validator
btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946 --amount 1000 --no_prompt

# Ensure both the miner and validator keys are successfully registered.
btcli subnet list --subtensor.chain_endpoint ws://127.0.0.1:9946
btcli wallet overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

cd ../bittensor-subnet-template


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
    tmux split-window -v -t 0 'python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name3 validator --wallet.hotkey default --logging.debug'
fi
