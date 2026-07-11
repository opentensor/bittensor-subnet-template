> [!IMPORTANT]
> **This repository is archived and no longer maintained.**
>
> This template targets the legacy Bittensor SDK (v10) and its `Axon`/`Dendrite`/`Synapse` networking stack, which was removed in Bittensor 11. It will not work with current releases.
>
> To build a subnet against Bittensor 11, see the [migration guide](https://bittensor.com/docs/migration) and the [signed requests guide](https://bittensor.com/docs/guides/signed-requests) for the replacement identity layer.

<div align="center">

# **Bittensor Subnet Template** <!-- omit in toc -->
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

---

## The Incentivized Internet <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)
</div>

---
- [Quickstarter template](#quickstarter-template)
- [Introduction](#introduction)
  - [Example](#example)
- [Installation](#installation)
  - [Before you proceed](#before-you-proceed)
  - [Install](#install)
- [Writing your own incentive mechanism](#writing-your-own-incentive-mechanism)
- [Running this subnet (validator + miner)](#running-this-subnet-validator--miner)
- [Writing your own subnet API](#writing-your-own-subnet-api)
- [Subnet Links](#subnet-links)
- [License](#license)

---
## Quickstarter template

This template contains all the required installation instructions, scripts, and files and functions for:
- Building Bittensor subnets.
- Creating custom incentive mechanisms and running these mechanisms on the subnets. 

In order to simplify the building of subnets, this template abstracts away the complexity of the underlying blockchain and other boilerplate code. While the default behavior of the template is sufficient for a simple subnet, you should customize the template in order to meet your specific requirements.
---

## Introduction

**IMPORTANT**: If you are new to Bittensor subnets, read this section before proceeding to [Installation](#installation) section. 

The Bittensor blockchain hosts multiple self-contained incentive mechanisms called **subnets**. Subnets are playing fields in which:
- Subnet miners who produce value, and
- Subnet validators who produce consensus

determine together the proper distribution of TAO for the purpose of incentivizing the creation of value, i.e., generating digital commodities, such as intelligence or data. 

Each subnet consists of:
- Subnet miners and subnet validators.
- A protocol using which the subnet miners and subnet validators interact with one another. This protocol is part of the incentive mechanism.
- The Bittensor API using which the subnet miners and subnet validators interact with Bittensor's onchain consensus engine [Yuma Consensus](https://bittensor.com/documentation/validating/yuma-consensus). The Yuma Consensus is designed to drive these actors: subnet validators and subnet miners, into agreement on who is creating value and what that value is worth. 

### This subnet: Inference-as-a-Service

This subnet is designed for model inference. Validators send prompts, miners return responses, and validators score responses against expected outputs. Miners can choose any model they want to run (including fine-tuned variants) and report the model name back to validators. By default, miners use placeholder responses, but you can replace the miner logic with a real model or inference service. The incentive mechanism rewards correct responses and can be extended to include latency or quality metrics.

This starter template is split into three primary files. To write your own incentive mechanism, you should edit these files. These files are:
1. `template/protocol.py`: Contains the definition of the protocol used by subnet miners and subnet validators.
2. `neurons/miner.py`: Script that defines the subnet miner's behavior, i.e., how the subnet miner responds to requests from subnet validators.
3. `neurons/validator.py`: This script defines the subnet validator's behavior, i.e., how the subnet validator requests information from the subnet miners and determines the scores.

### Example

The Bittensor Subnet 1 for Text Prompting is built using this template. See [prompting](https://github.com/macrocosm-os/prompting) for how to configure the files and how to add monitoring and telemetry and support multiple miner types. Also see this Subnet 1 in action on [Taostats](https://taostats.io/subnets/netuid-1/) explorer.

---

## Installation

### Before you proceed
Before you proceed with the installation of the subnet, note the following: 

- Use these instructions to run your subnet locally for your development and testing, or on Bittensor testnet or on Bittensor mainnet. 
- **IMPORTANT**: We **strongly recommend** that you first run your subnet locally and complete your development and testing before running the subnet on Bittensor testnet. Furthermore, make sure that you next run your subnet on Bittensor testnet before running it on the Bittensor mainnet.
- You can run your subnet either as a subnet owner, or as a subnet validator or as a subnet miner. 
- **IMPORTANT:** Make sure you are aware of the minimum compute requirements for your subnet. See the [Minimum compute YAML configuration](./min_compute.yml).
- Note that installation instructions differ based on your situation: For example, installing for local development and testing will require a few additional steps compared to installing for testnet. Similarly, installation instructions differ for a subnet owner vs a validator or a miner. 

### Install

- **Running locally**: Follow the step-by-step instructions described in this section: [Running Subnet Locally](./docs/running_on_staging.md).
- **Running on Bittensor testnet**: Follow the step-by-step instructions described in this section: [Running on the Test Network](./docs/running_on_testnet.md).
- **Running on Bittensor mainnet**: Follow the step-by-step instructions described in this section: [Running on the Main Network](./docs/running_on_mainnet.md).

---

## Writing your own incentive mechanism

As described in [Quickstarter template](#quickstarter-template) section above, when you are ready to write your own incentive mechanism, update this template repository by editing the following files. The code in these files contains detailed documentation on how to update the template. Read the documentation in each of the files to understand how to update the template. There are multiple **TODO**s in each of the files identifying sections you should update. These files are:
- `template/protocol.py`: Contains the definition of the wire-protocol used by miners and validators.
- `neurons/miner.py`: Script that defines the miner's behavior, i.e., how the miner responds to requests from validators.
- `neurons/validator.py`: This script defines the validator's behavior, i.e., how the validator requests information from the miners and determines the scores.
- `template/forward.py`: Contains the definition of the validator's forward pass.
- `template/reward.py`: Contains the definition of how validators reward miner responses.
- `template/validator/forward.py`: Contains the definition of the validator's forward pass.
- `template/validator/reward.py`: Contains the definition of how validators reward miner responses.

In addition to the above files, you should also update the following files:
- `README.md`: This file contains the documentation for your project. Update this file to reflect your project's documentation.
- `CONTRIBUTING.md`: This file contains the instructions for contributing to your project. Update this file to reflect your project's contribution guidelines.
- `template/__init__.py`: This file contains the version of your project.
- `setup.py`: This file contains the metadata about your project. Update this file to reflect your project's metadata.
- `docs/`: This directory contains the documentation for your project. Update this directory to reflect your project's documentation.

__Note__
The `template` directory should also be renamed to your project name.
---

## Running this subnet (validator + miner)

Follow the full local/testnet/mainnet setup instructions in the docs linked above. Once your wallets are created and registered, you can run a validator and miner for this inference subnet.

### Run a miner

```bash
python neurons/miner.py --netuid <NETUID> --wallet.name miner --wallet.hotkey default --logging.debug
```

Optional: report the model you are running. This is not enforced but helps validators understand miner behavior:

```bash
export MINER_MODEL_NAME="my-llama3-8b-finetune"
python neurons/miner.py --netuid <NETUID> --wallet.name miner --wallet.hotkey default --logging.debug
```

### Run a validator

```bash
python neurons/validator.py --netuid <NETUID> --wallet.name validator --wallet.hotkey default --logging.debug
```

### How scoring works

Validators sample inference tasks, send prompts to miners, and compare responses to expected outputs. Correct responses receive higher rewards. You can expand this logic in `template/validator/reward.py` to include latency, safety checks, or more complex grading.

# Writing your own subnet API
To leverage the abstract `SubnetsAPI` in Bittensor, you can implement a standardized interface. This interface is used to interact with the Bittensor network and can be used by a client to interact with the subnet through its exposed axons.

What does Bittensor communication entail? Typically two processes, (1) preparing data for transit (creating and filling `synapse`s) and (2), processing the responses received from the `axon`(s).

This protocol uses a handler registry system to associate bespoke interfaces for subnets by implementing two simple abstract functions:
- `prepare_synapse`
- `process_responses`

These can be implemented as extensions of the generic `SubnetsAPI` interface.  E.g.:


This is abstract, generic, and takes(`*args`, `**kwargs`) for flexibility. See the extremely simple base class:
```python
class SubnetsAPI(ABC):
    def __init__(self, wallet: "bt.wallet"):
        self.wallet = wallet
        self.dendrite = bt.dendrite(wallet=wallet)

    async def __call__(self, *args, **kwargs):
        return await self.query_api(*args, **kwargs)

    @abstractmethod
    def prepare_synapse(self, *args, **kwargs) -> Any:
        """
