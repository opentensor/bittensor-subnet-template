# Running Subnet Locally

This tutorial will guide you through setting up a local blockchain (subtensor), creating a subnet, and run your incentive mechanism on the subnet.

## Prerequisites

Before proceeding further, make sure that you have installed Bittensor. See the below instructions:

- [Install `bittensor`](https://github.com/opentensor/bittensor#install).

After installing `bittensor`, proceed as below:

## 1. Install substrate dependencies
Begin by installing the required dependencies for running a substrate node.
```bash
# Instructions for Linux
# Update your system packages
sudo apt update 

# Install additional required libraries and tools
sudo apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler
```

## 2. Install Rust and Cargo
Rust is the programming language used in substrate development, and Cargo is Rust's package manager.
```bash
# Install rust and cargo
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Update your shell's source to include Cargo's path
source "$HOME/.cargo/env"
```

## 3. Clone the subtensor repository
This step fetches the subtensor codebase to your local machine.
```bash
git clone https://github.com/opentensor/subtensor.git
```

## 4. Switch to the user-creation branch
Navigate into the repository and switch to the desired branch.
```bash
cd subtensor
git fetch origin subnets/user-creation
git checkout subnets/user-creation
```

## 5. Setup Rust for Substrate development
Ensure you have the nightly toolchain and the WebAssembly (wasm) compilation target. Note that this step will run the subtensor chain on your terminal directly, hence we advise that you run this as a background process using PM2 or other software.
```bash
# Update to the nightly version of rust
./subtensor/scripts/init.sh
```

## 6. Initialize 

Initialize your local subtensor chain in development mode. This command will set up and run a local subtensor network.
```bash
./scripts/localnet.sh
```
*Note: Watch for any build or initialization outputs here. If building the project for the first time, this step will take while to finish building depending on your hardware.*

## 7. Install subnet template

```bash
# Navigate to your project directory
# Clone the template repository
git clone https://github.com/opentensor/bittensor-subnet-template.git

# Navigate to the cloned repository
cd bittensor-subnet-template

# Install the bittensor-subnet-template python package
python -m pip install -e .
```

## 8. Set up wallets
You'll need wallets for different roles in the subnetwork. The owner wallet creates and controls the subnet. The validator and miner will run the respective validator/miner scripts and be registered to the subnetwork created by the owner.
```bash
# Create a coldkey for the owner role
btcli wallet new_coldkey --wallet.name owner

# Set up the miner's wallets
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default

# Set up the validator's wallets
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default
```

## 9. Mint tokens from faucet
You will need tokens to initialize the intentive mechanism on the chain as well as registering a network (below). 
Run the following command to mint yourself tokens on your chain.
```bash
# Mint tokens for the owner
btcli wallet faucet --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Balance: τ0.000000000 ➡ τ100.000000000
# Mint tokens to your validator.
btcli wallet faucet --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Balance: τ0.000000000 ➡ τ100.000000000
```

## 10. Create a subnetwork
The commands below establish a new subnetwork on the local chain. The cost will be exactly τ100.000000000 for the first network you create.
```bash
btcli subnet create --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Your balance is: τ200.000000000
>> Do you want to register a subnet for τ100.000000000? [y/n]: 
>> Enter password to unlock key: [YOUR_PASSWORD]
>> ✅ Registered subnetwork with netuid: 1
```
*Note: The local chain will now have a default netuid of 1, the second registration will create netuid 2 and so on until you reach the subnet limit of 8. After this point the subnetwork with the least staked TAO will be replaced the incoming one.*

## 11. Register your subnet validator and subnet miner Keys
Enroll your subnet validator and subnet miner on the network. This gives your two keys unique slots on the subnetwork which has a current limit of 128 slots.
```bash
# Register the subnet miner
btcli subnet recycle_register --wallet.name miner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): 1
>> Continue Registration? [y/n]: y
>> ✅ Registered

# Register the subnet validator
btcli subnet recycle_register --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): 1
>> Continue Registration? [y/n]: y
>> ✅ Registered
```

## 11. Stake to your subnet validator
This bootstraps the incentives on your new subnet by adding stake into its incentive mechanism.
```bash
btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Stake all Tao from account: 'validator'? [y/n]: y
>> Stake:
    τ0.000000000 ➡ τ100.000000000
```

## 12. Validate your key registrations on your new subnet
Ensure both the miner and validator keys are successfully registered.
```bash
btcli subnet list --subtensor.chain_endpoint ws://127.0.0.1:9946
                        Subnets - finney                             
NETUID  NEURONS  MAX_N   DIFFICULTY  TEMPO  CON_REQ  EMISSION  BURN(τ)  
   1        2     256.00   10.00 M    1000    None     0.00%    τ1.00000 
   2      128    

btcli wallet overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   100.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ100.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         

btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   

```

## 13. Run subnet miner and subnet validator
Make sure to specify your subnetwork parameters.
```bash
python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug
>> ... # Run logs.
python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug
>> ... # Run logs.
```

## 14. Verify your incentive mechanism is running
After a few blocks you validators will set weights this enables the mechanism. Then after the subnet tempo elapses (300 block ~1hrs ) you should see your incentive mechanism beginning to distribute TAO to your miner.
```bash
btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946
```

## Ending your session
If you wish to halt your nodes:
```bash
# Press CTRL + C keys in the terminal.
```

---
