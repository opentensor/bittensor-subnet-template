# Running on Staging Network
This tutorial shows how to run your own subtensor chain locally, create a subnetwork and connect your mechanism to it.

## Steps

1. Install substrate dependencies
This installs the dependencies needed to build and run a substrate node.
```bash
$ sudo apt-get update 
$ sudo apt install build-essential
$ sudo apt-get install clang
$ sudo apt-get install curl 
$ sudo apt-get install git 
$ sudo apt-get install make
$ sudo apt install --assume-yes git clang curl libssl-dev protobuf-compiler
$ sudo apt install --assume-yes git clang curl libssl-dev llvm libudev-dev make protobuf-compiler
```

2. Install Rust and Cargo
This installs rust and cargo, the rust package manager.
```bash
$ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
$ source "$HOME/.cargo/env"
```

3. Install rust nightly toolchain and wasm target.
This sets up your rust version to nightly and adds the wasm target.
```bash
$ rustup update nightly
$ rustup target add wasm32-unknown-unknown --toolchain nightly
```

4. Clone the subtensor repository
This clones the subtensor code base into your local repo.
```bash
$ git clone https://github.com/opentensor/subtensor.git
```

5. Clone Subtensor
This pulls the user-creation branch.
```bash
$ cd subtensor
$ git fetch origin subnets/user-creation; git checkout subnets/user-creation
```

6. Run a the built Subtensor node for init your chain in dev mode
This builds and runs a local network.
```bash
$ ./scripts/localnet.sh
>>> ... # build and chain output.
```

7. Clone and Install Bittensor revolution
This clones and installs the template if you dont already have it (if you do, skip this step)
```bash
$ cd .. # back out of the subtensor repo
$ git clone https://github.com/opentensor/bittensor-subnet-template.git # Clone the bittensor-subnet-template repo
$ cd bittensor-subnet-template # Enter the bittensor-subnet-template repo
$ python -m pip install -e . # Install the bittensor-subnet-template package
```

8. Create wallets for your subnet owner, for your validator and for your miner.
This creates local coldkey and hotkey pairs for your 3 identities.
```bash
# Create a coldkey for your owner wallet.
$ btcli new_coldkey --wallet.name owner

# Create a coldkey and hotkey for your miner wallet.
$ btcli new_coldkey --wallet.name miner
$ btcli new_hotkey --wallet.name miner --wallet.hotkey default

# Create a coldkey and hotkey for your validator wallet.
$ btcli new_coldkey --wallet.name validator
$ btcli new_hotkey --wallet.name validator --wallet.hotkey default
```

9. Create a subnetwork
This creates a subnetwork on the local chain on netuid 1.
```bash
# Run the register subnetwork command on the locally running chain.
$ btcli register_subnet --subtensor.chain_endpoint ws://127.0.0.1:9946 
# Enter the owner wallet name which gives permissions to the coldkey to later define running hyper parameters.
>> Enter wallet name (default): owner # Enter your owner wallet name
>> Enter password to unlock key: # Enter your wallet password.
>> Register subnet? [y/n]: <y/n> # Select yes (y)
>> ⠇ 📡 Registering subnet...
✅ Registered subnetwork # Your subnet will be registered on netuid = 1 because you are running a local chain.
```

10. Register your validator and miner keys to the networks.
This registers your validator and miner keys to the network giving them the first 2 slots on the network.
```bash
# Register your miner key to the network.
$ btcli register --wallet.name miner --wallet.hotkey default  --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ⠦ 📡 Submitting POW...
>> ✅ Registered

# Register your validator key to the network.
$ btcli register --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946
>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ⠦ 📡 Submitting POW...
>> ✅ Registered
```

11. Check that your keys have been registered.
This returns information about your registered keys.
```bash
# Check that your validator key has been registered.
$ btcli overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         

# Check that your miner has been registered.
$ btcli overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   
```

10. Edit the default `NETUID=1` and `CHAIN_ENDPOINT=ws://127.0.0.1:9946` arguments in `template/__init__.py` to match your created subnetwork.
Or run the miner and validator directly with the netuid and chain_endpoint arguments.
```bash
# Run the miner with the netuid and chain_endpoint arguments.
$ python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running miner for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...

# Run the validator with the netuid and chain_endpoint arguments.
$ python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running validator for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...
```

7. Stopping Your Nodes:
If you want to stop your nodes, you can do so by pressing CTRL + C in the terminal where the nodes are running.
