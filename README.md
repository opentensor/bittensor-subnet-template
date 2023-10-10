<div align="center">

# **Bittensor Subnet Template** <!-- omit in toc -->
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

---

### The Incentivized Internet <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)
</div>

---
- [Quickstarter template](#quickstarter-template)
  - [Introduction](#introduction)
- [Installation](#installation)
  - [Before you proceed](#before-you-proceed)
  - [Install](#install)
- [Writing your own incentive mechanism](#writing-your-own-incentive-mechanism)
- [License](#license)

---

This template contains all the required installation instructions, scripts, and files and functions for:
- Building Bittensor subnets.
- Creating custom incentive mechanisms and running these mechanisms on the subnets. 

---

## Quickstarter template

### Introduction

**IMPORTANT**: If you are new to Bittensor subnets, read this section before proceeding to [Installation](#installation) section. 

The Bittensor blockchain hosts multiple self-contained incentive mechanisms called **subnets**. Subnets are playing fields in which miners, those producing value, and validators, those producing consensus, determine together the proper distribution of TAO for the purpose of incentivizing the creation of value, i.e., generating digital commodities, such as intelligence or data. 

Each subnet consists of:
- A wire protocol through which miners and validators interact.
- The method of interactions of miners and validators with Bittensor's chain consensus engine [Yuma Consensus](https://bittensor.com/documentation/validating/yuma-consensus). The Yuma Consensus is designed to drive these actors, validators and miners, into agreement on who is creating value. 

When you are ready to write your own custom incentive mechanism, start with this starter template repository. It is preloaded with all the files you need to run a very simple incentive mechanism. This simple incentive mechanism rewards miners for responding with the multiple of the value sent by validators. 

This simple starter template is split into three primary files. To write your own incentive mechanism, you should edit these files. These files are:
- `template/protocol.py`: Contains the definition of the wire-protocol used by miners and validators.
- `neurons/miner.py`: Script that defines the miner's behavior, i.e., how the miner responds to requests from validators.
- `neurons/validator.py`: This script defines the validator's behavior, i.e., how the validator requests information from the miners and determines the scores.

---

## Installation

### Before you proceed
Before you proceed with the installation of the subnet, note the following: 

- Following these instructions you can run your subnet locally for your development and testing, or on Bittensor testnet. We do **recommend** that you first run your subnet locally and finish your development and testing before running the subnet on Bittensor testnet. 
- You can also run your subnet either as a subnet owner, or as a validator or as a miner. 
- **IMPORTANT:** Make sure you are aware of the minimum compute requirements for your subnet. See the [Minimum compute YAML configuration](./min_compute.yml).
- Note that installation instructions differ based on your situation: For example, installing for local development and testing will require a few additional steps compared to installing for testnet. Similarly, installation instructions differ for a subnet owner vs a validator or a miner. 

### Install

- **Running locally**: Follow the step-by-step instructions described in this section: [Running Your Own Subtensor Chain Locally](./docs/running_on_staging.md).
- **Running on Bittensor testnet**: Follow the step-by-step instructions described in this section: [Running on the Testing Network](./docs/running_on_testnet.md).

---

## Writing your own incentive mechanism

As described in [Quickstarter template](#quickstarter-template) section above, when you are ready to write your own incentive mechanism, update this template repository by editing the following files. The code in these files contains detailed documentation on how to update the template. Read the documentation in each of the files to understand how to update the template. There are multiple **TODO**s in each of the files identifying sections you should update. These files are:
- `template/protocol.py`: Contains the definition of the wire-protocol used by miners and validators.
- `neurons/miner.py`: Script that defines the miner's behavior, i.e., how the miner responds to requests from validators.
- `neurons/validator.py`: This script defines the validator's behavior, i.e., how the validator requests information from the miners and determines the scores.

---

## License
This repository is licensed under the MIT License.
```text
# The MIT License (MIT)
# Copyright © 2023 Yuma Rao

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
```
