# Running on Staging Network
This tutorial shows how to run your own subtensor chain locally, create a subnetwork and connect your mechanism to it.

## Steps

1. Install substrate dependencies
This installs the dependencies needed to build and run a substrate node.
```bash
sudo apt-get update 
sudo apt install build-essential
sudo apt-get install clang
sudo apt-get install curl 
sudo apt-get install git 
sudo apt-get install make
sudo apt install --assume-yes git clang curl libssl-dev protobuf-compiler
sudo apt install --assume-yes git clang curl libssl-dev llvm libudev-dev make protobuf-compiler
```

2. Install Rust and Cargo
This installs rust and cargo, the rust package manager.
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

3. Install rust nightly toolchain and wasm target.
This sets up your rust version to nightly and adds the wasm target.
```bash
rustup update nightly
rustup target add wasm32-unknown-unknown --toolchain nightly
```

4. Clone the subtensor repository
This clones the subtensor code base into your local repo.
```bash
git clone https://github.com/opentensor/subtensor.git
```

5. Build Subtensor
This pulls the user-creation branch and builds the node.
```bash
cd subtensor
git fetch origin subnets/user-creation; git checkout subnets/user-creation
cargo build --release
```

6. Run a the built Subtensor node for init your chain in dev mode
This runs the built node with the `--tmp` flag, which creates a temporary node (meaning it won't persist data across runs).
```bash
./target/release/node-subtensor --tmp
./target/release/node-subtensor --help # For more info.
>>> 2023-08-08 16:41:57 Subtensor Node    
>>> ...  
>>> 2023-08-08 16:42:03 💤 Idle (0 peers), best: #0 (0x0e5c…912d), finalized #0 (0x0e5c…912d), ⬇ 0 ⬆ 0 
```
`--tmp` creates a temporary node (meaning it won't persist data across runs).

7. Clone and Install Bittensor revolution
```bash
cd .. # back out of the subtensor repo
git clone https://github.com/opentensor/bittensor-subnet-template.git # Clone the bittensor-subnet-template repo
cd bittensor-subnet-template # Enter the bittensor-subnet-template repo
python -m pip install -e . # Install the bittensor-subnet-template package
```

8. Create a subnetwork
```bash
btcli register_subnet --subtensor.network local # Run the register subnetwork command on the locally running chain.
# Enter the wallet name you want to use (if you dont have one, create one with btcli new_coldkey and btcli new_hotkey)
# the coldkey you use here will own the subnetwork and can later define its running hyper parameters.
>> Enter wallet name (default): <your wallet name> 
>> Register subnet? [y/n]: <y/n> # Select yes (y)
>> ⠇ 📡 Registering subnet...
```

9. List subnetworks to see your created netuid.
```bash
btcli list_subnets
```

10. Edit the default NETUID and CHAIN_ENDPOINT arguments in `template/__init__.py` to match your created subnetwork.
Or run the miner and validator directly with the netuid and chain_endpoint arguments.
```bash
python template/miner.py --netuid <your netuid> --chain_endpoint wss://0.0.0.0:9944
python template/validator.py --netuid <your netuid> --chain_endpoint ws:s//0.0.0.0:9944

```

7. Stopping Your Nodes:
If you want to stop your nodes, you can do so by pressing CTRL + C in the terminal where the nodes are running.
