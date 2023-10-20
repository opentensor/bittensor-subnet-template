# Running Subnet on Test Network

This tutorial shows how to use the Bittensor test network to create a subnet and run your incentive mechanism on it. 

**IMPORTANT:** We strongly recommend that you first run [Running Subnet Locally](running_on_staging.md) before running on the testnet. Incentive mechanisms running on the testnet are open to anyone, and although these mechanisms on testnet do not emit real TAO, they cost you test TAO which you must create. 

**DANGER**
- Do not expose your private keys.
- Only use your testnet wallet.
- Do not reuse the password of your mainnet wallet.
- Make sure your incentive mechanism is resistant to abuse. 

## Prerequisites

Before proceeding further, make sure that you have installed Bittensor. See the below instructions:

- [Install `bittensor`](https://github.com/opentensor/bittensor#install).

After installing `bittensor`, proceed as below:

## 1. Install Bittensor subnet template

**Skip this step if** you already did this during local testing and development.

```bash
# In your project directory
git clone https://github.com/opentensor/bittensor-subnet-template.git # Clone the bittensor-subnet-template repo
cd bittensor-subnet-template # Enter the bittensor-subnet-template repo directory
python -m pip install -e . # Install the bittensor-subnet-template package
```

## 2. Create wallets 

Create wallets for your subnet owner, for your subnet validator and for your subnet miner.
  
This creates local coldkey and hotkey pairs for your three identities: subnet owner, subnet validator and subnet miner. 

The owner will create and control the subnet and must have at least 100 test net TAO on it before it can run next steps. 

The subnet validator and subnet miner will run the respective validator and miner scripts and be registered to the subnetwork created by the owner.

```bash
# Create a coldkey for your owner wallet.
btcli wallet new_coldkey --wallet.name owner

# Create a coldkey and hotkey for your miner wallet.
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default

# Create a coldkey and hotkey for your validator wallet.
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default
```

## 3. Getting the price of subnetwork creation

Creating subnetworks on the testnet is competitive. The cost is determined by the rate at which new networks are being registered onto the chain. 

By default you must have at least 100 testnet TAO in your owner wallet to create a subnetwork. However the exact amount will fluctuate based on demand. The below command shows how to get the current price of creating a subnetwork.

```bash
btcli subnet lock_cost --subtensor.network test
>> Subnet lock cost: τ100.000000000
```

## 4. (Optional) Getting faucet tokens
   
If you do not have enough faucet tokens to create a test subnet you can create additional testnet faucet tokens. The code below shows how to get faucet tokens.

```bash
btcli wallet faucet --wallet.name owner --subtensor.network test
>> Balance: τ0.000000000 ➡ τ100.000000000
>> Balance: τ100.000000000 ➡ τ200.000000000
...
```

## 5. Purchasing a slot

Using the test TAO from the previous step you can register your subnet to the chain. This will create a new subnet on the chain and give you the owner permissions to it. 

The below code shows how to purchase a slot. 

**NOTE**: Slots cost TAO, and you will not get this TAO back. Instead, this TAO is recycled back into your incentive mechanism, to be later mined.

```bash
# Run the register subnetwork command on the locally running chain.
btcli subnet create --subtensor.network test 
# Enter the owner wallet name which gives permissions to the coldkey to later define running hyper parameters.
>> Enter wallet name (default): owner # Enter your owner wallet name
>> Enter password to unlock key: # Enter your wallet password.
>> Register subnet? [y/n]: <y/n> # Select yes (y)
>> ⠇ 📡 Registering subnet...
✅ Registered subnetwork with netuid: 1 # Your subnet netuid will show here, save this for later.
```

## 6.  Register your subnet validator and subnet miner keys

This step registers your subnet validator and subnet miner keys to the network, giving them the **first two slots** on the network.

```bash
# Register your miner key to the network.
btcli subnet recycle_register --netuid 13 --subtensor.network test --wallet.name miner --wallet.hotkey default
>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ✅ Registered

# Register your validator key to the network.
btcli subnet recycle_register --netuid 13 --subtensor.network test --wallet.name validator --wallet.hotkey default
>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ✅ Registered
```

## 7. Check that your keys have been registered

This step returns information about your registered keys.

```bash
# Check that your validator key has been registered.
btcli wallet overview --wallet.name validator --subtensor.network test
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         

# Check that your miner has been registered.
btcli wallet overview --wallet.name miner --subtensor.network test
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   
```

## 8. Edit the default arguments

Edit `NETUID=1` and `CHAIN_ENDPOINT=ws://127.0.0.1:9946` arguments in `template/__init__.py` to match your created subnetwork. Or run the subnet miner and subnet validator directly with the `netuid` and `chain_endpoint` arguments.
```bash
# Run the miner with the netuid and chain_endpoint arguments.
python neurons/miner.py --netuid 1 --subtensor.network test --wallet.name miner --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running miner for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...

# Run the validator with the netuid and chain_endpoint arguments.
python neurons/validator.py --netuid 1 --subtensor.network test --wallet.name validator --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running validator for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...
```

## 9. Stopping your nodes:
If you want to stop your nodes, you can do so by pressing CTRL + C in the terminal where the nodes are running.

## 10 Get emissions flowing

Register to the root network using the `btcli`:
```bash
btcli root register --subtensor.network test # ensure on testnet
```

Then set your weights for the subnet:
```bash
btcli root weights --subtensor.network test # ensure on testnet
```