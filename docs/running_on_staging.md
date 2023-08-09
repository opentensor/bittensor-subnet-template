## Running Your Own Subtensor Chain Locally

This tutorial will guide you through setting up a local subtensor chain, creating a subnetwork, and connecting your mechanism to it.

### 1. Install substrate dependencies
Begin by installing the required dependencies for running a substrate node.
```bash
# Update your system packages
$ sudo apt-get update 

# Install additional required libraries and tools
$ sudo apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler
```

### 2. Install Rust and Cargo
Rust is the programming language used in substrate development, and Cargo is Rust's package manager.
```bash
# Install rust and cargo
$ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Update your shell's source to include Cargo's path
$ source "$HOME/.cargo/env"
```

### 3. Setup Rust for Substrate Development
Ensure you have the nightly toolchain and the WebAssembly (wasm) compilation target.
```bash
# Update to the nightly version of rust
$ rustup update nightly

# Add wasm compilation target for the nightly toolchain
$ rustup target add wasm32-unknown-unknown --toolchain nightly
```

### 4. Clone the Subtensor Repository
This step fetches the subtensor codebase to your local machine.
```bash
$ git clone https://github.com/opentensor/subtensor.git
```

### 5. Switch to the User-Creation Branch
Navigate into the repository and switch to the desired branch.
```bash
$ cd subtensor
$ git fetch origin subnets/user-creation
$ git checkout subnets/user-creation
```

### 6. Initialize Your Local Subtensor Chain in Development Mode
This command will set up and run a local subtensor network.
```bash
$ ./scripts/localnet.sh
```
*Note: Watch for any build or initialization outputs here.*

### 7. Clone and Setup Bittensor Revolution
If you don't already have the Bittensor revolution, follow these steps.
```bash
# Navigate to your workspace root
$ cd ..

# Clone the template repository
$ git clone https://github.com/opentensor/bittensor-subnet-template.git

# Navigate to the cloned repository
$ cd bittensor-subnet-template

# Install the bittensor-subnet-template python package
$ python -m pip install -e .
```

### 8. Set Up Wallets
You'll need wallets for different roles in the subnetwork. The owner wallet creates and controls the subnet. The validator and miner will run the respective validator/miner scripts and be registered to the subnetwork created by the owner.
```bash
# Create a coldkey for the owner role
$ btcli new_coldkey --wallet.name owner

# Set up the miner's wallets
$ btcli new_coldkey --wallet.name miner
$ btcli new_hotkey --wallet.name miner --wallet.hotkey default

# Set up the validator's wallets
$ btcli new_coldkey --wallet.name validator
$ btcli new_hotkey --wallet.name validator --wallet.hotkey default
```

### 9. Create a Subnetwork
Establish a new subnetwork on the local chain.
```bash
$ btcli register_subnet --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Enter wallet name (default): owner 
>> Enter password to unlock key: [YOUR_PASSWORD]
>> Register subnet? [y/n]: y
>> ✅ Registered
```
*Note: The local chain will have a default netuid of 1, the second registration will have netuid 2 and so on.*

### 10. Register Your Validator and Miner Keys
Enroll your validator and miner on the network.
```bash
# Register the miner
$ btcli register --wallet.name miner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): 1
>> Continue Registration? [y/n]: y
>> ⠦ 📡 Submitting POW...
>> ✅ Registered


# Register the validator
$ btcli register --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): 1
>> Continue Registration? [y/n]: y
>> ⠦ 📡 Submitting POW...
>> ✅ Registered

```

### 11. Validate Your Key Registrations
Ensure both the miner and validator keys are successfully registered.
```bash
$ btcli overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         

$ btcli overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   

```

### 12. Run Miner and Validator
Make sure to specify your subnetwork parameters.
```bash
$ python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug
$ python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug
```

### Ending Your Session
If you wish to halt your nodes:
```bash
# Simply use the CTRL + C command in the terminal.
```

---

With these steps, you should be up and running with your own local Subtensor chain.