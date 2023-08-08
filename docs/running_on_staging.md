# Running on Staging Network
This tutorial is to take you through running

## Installing and Running Subtensor Locally
1. #### Prerequisites:
Ensure you have `Rust` and `Cargo` installed. If not, you can install them using [`Rustup`](https://doc.rust-lang.org/cargo/getting-started/installation.html).
You will also need `git` to clone the Subtensor repository.

2. #### Clone the Bittensor Repository:
```bash
git clone https://github.com/opentensor/bittensor.git
cd bittensor
```

3. #### Build Subtensor:
Navigate to the subtensor directory (if it exists in the repository) and then build it:
```
cd subtensor
cargo build --release
```

4. #### Run a Local Subtensor Node:
Once the build process is complete, you can run a local Subtensor node with:
```
./target/release/subtensor --tmp
```
`--tmp` creates a temporary node (meaning it won't persist data across runs).

5. #### Interacting with Your Node:
If you want to interact with your node, you'll likely need to use the Polkadot/Substrate frontend. You can run this locally or use the hosted version.
Configure the frontend to point to your local node (`localhost:9944`by default).

6. #### Further Configuration:
The above steps will get a subtensor node up and running with default configurations. However, Subtensor (like other Substrate-based projects) supports various flags and configurations. Use:
```
./target/release/subtensor --help
```
to see a list of all available flags and options.

7. Stopping Your Node:
If you want to stop your node, you can usually do so by pressing CTRL + C in the terminal where the node is running.
