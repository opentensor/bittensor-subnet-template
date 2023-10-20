# Running Subnet on Main Network
This tutorial shows how to use the bittensor `btcli` to create a subnetwork and connect your incentive mechanism to it. 

**IMPORTANT:** Before attempting to register on mainnet, we strongly recommend that you:
- First run [Running Subnet Locally](running_on_staging.md), and
- Then run [Running on the Test Network](running_on_testnet.md).

Your incentive mechanisms running on the main are open to anyone. They emit real TAO, and creating these mechanisms incur a `lock_cost` in TAO.

**DANGER**
- Do not expose your private keys.
- Only use your testnet wallet.
- Do not reuse the password of your mainnet wallet.
- Make sure your incentive mechanism is resistant to abuse. 

## Prerequisites

Before proceeding further, make sure that you have installed Bittensor. See the below instructions:

- [Install `bittensor`](https://github.com/opentensor/bittensor#install).

After installing `bittensor`, proceed as below:

## Steps

## 1. Install your subnet template

**Skip this step if** you already did this during local testing and development.

```bash
# In your project directory
git clone https://github.com/opentensor/bittensor-subnet-template.git # TODO[owner]: Replace this with your custom repo URL
cd bittensor-subnet-template # Enter your subnet template repo directory
python -m pip install -e . # Install your subnet template package
```

## 2. Create wallets 

Create wallets for your subnet owner, for your subnet validator and for your subnet miner. This creates local coldkey and hotkey pairs for your three identities. 

The subnet owner will create and control the subnet and must have at least 100 TAO on it before it can run next steps. 

The subnet validator and subnet miner will run the respective validator/miner scripts and be registered to the subnetwork created by the owner.

**NOTE**: You can also use existing wallets to register. Creating new keys is shown here for reference.

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

Creating subnetworks on mainnet is competitive. The cost is determined by the rate at which new networks are being registered onto the Bittensor blockchain. 

By default you must have at least 100 TAO on your owner wallet to create a subnetwork. However, the exact amount will fluctuate based on demand. The below code shows how to get the current price of creating a subnetwork.

```bash
btcli subnet lock_cost 
>> Subnet lock cost: τ100.000000000
```

## 4. Purchasing a slot

Using your TAO balance, you can register your subnet to the chain. This will create a new subnet on the chain and give you the owner permissions to it. The below code shows how to purchase a slot. 

**NOTE**: Slots cost TAO to lock. You will get this TAO back when the subnet is dissolved.

```bash
# Run the register subnetwork command on the locally running chain.
btcli subnet create  
# Enter the owner wallet name which gives permissions to the coldkey to later define running hyper parameters.
>> Enter wallet name (default): owner # Enter your owner wallet name
>> Enter password to unlock key: # Enter your wallet password.
>> Register subnet? [y/n]: <y/n> # Select yes (y)
>> ⠇ 📡 Registering subnet...
✅ Registered subnetwork with netuid: 1 # Your subnet netuid will show here, save this for later.
```

## 5. (Optional) Register your subnet validator and subnet miner keys to the networks.

**NOTE**: While this is not enforced, we recommend subnet owners to run a subnet validator and a subnet miner on the network to demonstrate proper use to the community.

This step registers your subnet validator and subnet miner keys to the network giving them the **first two slots** on the network.

```bash
# Register your miner key to the network.
btcli subnet recycle_register --netuid 1 --subtensor.network finney --wallet.name miner --wallet.hotkey default
>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ✅ Registered

# Register your validator key to the network.
btcli subnet recycle_register --netuid 1 --subtensor.network finney --wallet.name validator --wallet.hotkey default

>> Enter netuid [1] (1): # Enter netuid 1 to specify the network you just created.
>> Continue Registration?
  hotkey:     ...
  coldkey:    ...
  network:    finney [y/n]: # Select yes (y)
>> ✅ Registered
```

## 6. Check that your keys have been registered

This returns information about your registered keys.
```bash
# Check that your subnet validator key has been registered.
btcli wallet overview --wallet.name validator 
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         

# Check that your subnet miner has been registered.
btcli wallet overview --wallet.name miner 
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   
```

## 7. Edit the default arguments

Edit the default arguments `NETUID=1` and `CHAIN_ENDPOINT=wss://entrypoint-finney.opentensor.ai:443` arguments in `template/__init__.py` to match your created subnetwork. Or run the subnet miner and subnet validator directly with the `netuid` and `chain_endpoint` arguments.
```bash
# Run the subnet miner with the netuid and chain_endpoint arguments.
python neurons/miner.py --netuid 1  --wallet.name miner --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running miner for subnet: 1 on network: wss://entrypoint-finney.opentensor.ai:443 with config: ...

# Run the subnet validator with the netuid and chain_endpoint arguments.
python neurons/validator.py --netuid 1  --wallet.name validator --wallet.hotkey default --logging.debug
>> 2023-08-08 16:58:11.223 |       INFO       | Running validator for subnet: 1 on network: wss://entrypoint-finney.opentensor.ai:443 with config: ...
```

## 8. Stopping your nodes
If you want to stop your nodes, you can do so by pressing CTRL + C in the terminal where the nodes are running.

## 9. Get emissions flowing

Register to the root network using the `btcli`:
```bash
btcli root register 
```

Then set your weights for the subnet:
```bash
btcli root weights 
```
---