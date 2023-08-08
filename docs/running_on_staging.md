# Running on Staging Network
This tutorial explains how to run your own subtensor chain locally, create a subnetwork and connect to it.

## Installing and running a fresh Subtensor locally

1. Install substrate dependencies
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
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

3. Install rust nightly toolchain and wasm target.
```bash
rustup update nightly
rustup target add wasm32-unknown-unknown --toolchain nightly
```

4. Clone the subtensor repository
```bash
git clone https://github.com/opentensor/subtensor.git
```

5. Build Subtensor
```bash
cd subtensor
git fetch origin subnets/user-creation; git checkout subnets/user-creation
cargo build --release
```

6. Run a the built Subtensor node for init your chain in dev mode:
```bash
./target/release/node-subtensor --tmp
./target/release/node-subtensor --help # For more info.
```
`--tmp` creates a temporary node (meaning it won't persist data across runs).

7. Install Bittensor revolution
```bash
python -m pip install git+https://github.com/opentensor/bittensor.git@revolution
```

8. Create a subnetwork
```bash
btcli create_subnetwork --subtensor.network local
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

7. Stopping Your Node:
If you want to stop your node, you can usually do so by pressing CTRL + C in the terminal where the node is running.
