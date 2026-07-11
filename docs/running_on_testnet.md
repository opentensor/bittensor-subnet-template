# Running Subnet on Testnet

This tutorial shows how to use the Bittensor testnet to create a subnet and run your incentive mechanism on it. 

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

**NOTE: Skip this step if** you already did this during local testing and development.

`cd` into your project directory and clone the bittensor-subnet-template repo:

```bash
git clone https://github.com/opentensor/bittensor-subnet-template.git 
```

Next, `cd` into bittensor-subnet-template repo directory:

```bash
cd bittensor-subnet-template # Enter the 
```

Install the bittensor-subnet-template package:

```bash
python -m pip install -e . 
```

## 2. Create wallets 

Create wallets for subnet owner, subnet validator and for subnet miner.
  
This step creates local coldkey and hotkey pairs for your three identities: subnet owner, subnet validator and subnet miner. 

The owner will create and control the subnet. The owner must have at least 100 testnet TAO before the owner can run next steps. 

The validator and miner will be registered to the subnet created by the owner. This ensures that the validator and miner can run the respective validator and miner scripts.

Create a coldkey for your owner wallet:

```bash
btcli wallet new-coldkey --wallet-name owner
```

Create a coldkey and hotkey for your miner wallet:

```bash
btcli wallet new-coldkey --wallet-name miner
```

and

```bash
btcli wallet new-hotkey --wallet-name miner --hotkey default
```

Create a coldkey and hotkey for your validator wallet:

```bash
btcli wallet new-coldkey --wallet-name validator
```

and

```bash
btcli wallet new-hotkey --wallet-name validator --hotkey default
```

## 3. Get the price of subnet creation

Creating subnets on the testnet is competitive. The cost is determined by the rate at which new subnets are being registered onto the chain. 

By default you must have at least 100 testnet TAO in your owner wallet to create a subnet. However, the exact amount will fluctuate based on demand. The below command shows how to get the current price of creating a subnet.

```bash
btcli subnets burn-cost --network test
```

The above command will show:

```bash
>> Subnet lock cost: τ100.000000000
```

## 4. (Optional) Get faucet tokens
   
Faucet is disabled on the testnet. Hence, if you don't have sufficient faucet tokens, ask the [Bittensor Discord community](https://discord.com/channels/799672011265015819/830068283314929684) for faucet tokens.

## 5. Purchase a slot

Using the test TAO from the previous step you can register your subnet on the testnet. This will create a new subnet on the testnet and give you the owner permissions to it. 

The below command shows how to purchase a slot. 

**NOTE**: Slots cost TAO to lock. You will get this TAO back when the subnet is deregistered.

```bash
btcli subnets create --network test --wallet-name owner
```

Follow the prompts to unlock your owner wallet and confirm the registration.
When successful, the command will return your subnet netuid. Save it for later.

## 6. Register keys

This step registers your subnet validator and subnet miner keys to the subnet, giving them the **first two slots** on the subnet.

Register your miner key to the subnet:

```bash
btcli subnets register --netuid <NETUID> --network test --wallet-name miner --hotkey default
```

Follow the prompts to confirm the registration.

Next, register your validator key to the subnet:

```bash
btcli subnets register --netuid <NETUID> --network test --wallet-name validator --hotkey default
```

Follow the prompts to confirm the registration.

## 7. Check that your keys have been registered

This step returns information about your registered keys.

Check that your validator key has been registered:

```bash
btcli wallet overview --wallet-name validator --network test
```

The above command will display the below:

```bash
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  0      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0         
```

Check that your miner has been registered:

```bash
btcli wallet overview --wallet-name miner --network test
```

The above command will display the below:

```bash
Subnet: 1                                                                                                                                                                
COLDKEY  HOTKEY   UID  ACTIVE  STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS  EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON  HOTKEY_SS58                    
miner    default  1      True   0.00000  0.00000  0.00000    0.00000    0.00000    0.00000            0  0.00000                14  none  5GTFrsEQfvTsh3WjiEVFeKzFTc2xcf…
1        1        2            τ0.00000  0.00000  0.00000    0.00000    0.00000    0.00000           ρ0  0.00000                                                         
                                                                          Wallet balance: τ0.0   
```

## 8. Run subnet miner and subnet validator

Run the subnet miner:

```bash
python neurons/miner.py --netuid <NETUID> --subtensor.network test --wallet.name miner --wallet.hotkey default --logging.debug
```

You will see the below terminal output:

```bash
>> 2023-08-08 16:58:11.223 |       INFO       | Running miner for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...
```

Next, run the subnet validator:

```bash
python neurons/validator.py --netuid <NETUID> --subtensor.network test --wallet.name validator --wallet.hotkey default --logging.debug
```

You will see the below terminal output:

```bash
>> 2023-08-08 16:58:11.223 |       INFO       | Running validator for subnet: 1 on network: ws://127.0.0.1:9946 with config: ...
```


## 9. Start emissions

Before starting emissions, check that the subnet can start:

```bash
btcli subnets check-start --netuid <NETUID> --network test
```

If the check passes, start emissions:

```bash
btcli subnets start --netuid <NETUID> --network test
```

## 10. Stopping your nodes

To stop your nodes, press CTRL + C in the terminal where the nodes are running.
