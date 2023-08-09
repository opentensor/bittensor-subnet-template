
<div align="center">

# **Bittensor Subnet Template** <!-- omit in toc -->
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

---

### Internet-scale Neural Networks <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)

</div>

---

This template contains all the necessary files and functions to define Bittensor subnet incentive mechanisms. You can run this template in three ways,
on Bittensor's main-network (real TAO), Bittensor's test-network (fake TAO), or with your own staging-network. This repo includes instructions for dong all three.

# Introduction
Before writing your own incentive mechanism for Bittensor be sure to familiarize yourself with how Bittensor incentive mechanisms work by reading about [Bittensor Incentive Mechanisms](https://bittensor.com/documentation/validating/yuma-consensus)

In a nutshell, Bittensor is composed of multiple self-contained incentive mechanisms through which miners (those producing value) and validators (those producing consensus) determine together the proper distribution of TAO (the network token, representing value and ownership in the network). This interaction is constructed based on the specific protocol defined in this repository by the subnetwork creator in conjunction with the chain consensus engine (Yuma Consensus) which is defined in [subtensor](https://github.com/opentensor/subtensor) and forces the validators to agree on the same distribution of TAO.

This repository is a template for writing such mechanisms, with the needed files preloaded to run a very simple mechanism to reward miners for responding with the multiple of the value sent by vaidators. This template is designed to be simple, merely as a starting point for those who want to write their own mechanism. It is split into 4 primary files which you should rewrite. (Note: you can also add additional files if you want to split your code into multiple files, but these 4 are the minimum needed) 
These files are:
- `template/__init__.py`: The file which defines the subnet name, protocol version, blockchain-endpoint and subnetwork uid.
- `template/protocol.py`: The file where the wire-protocol used by miners and validators is defined.
- `template/miner.py`: This script defines the miner's behavior, i.e., how the miner responds to requests from validators.
- `template/validator.py`: This script defines the validator's behavior, i.e., how the validator requests information from miners and determines scores.

</div>

---

# Installation
This repository requires python3.8 or higher. To install, simply clone this repository and install the requirements.
```bash
git clone https://github.com/opentensor/bittensor-subnet-template.git
cd bittensor-subnet-template
python -m pip install -r requirements.txt
python -m pip install -e .
```

</div>

---

# Running the template
Before running the template you will need to attain a subnetwork on either Bittensor's main network, test network, or your own staging network. To create subnetworks on each of these subnets follow the instructions in files below:
- `docs/running_on_staging.md`
- `docs/running_on_testnet.md`
- `docs/running_on_mainnet.md`

Once you have done this, you can run the miner and validator with the following commands.
```bash
python -m template.miner # To run the miner
python -m template.validator # To run the validator
```

</div>

---

# Updating the template
The code contains detailed documentation on how to update the template. Please read the documentation in each of the files to understand how to update the template. There are multiple TODOs in each of the files which you should read and update.

</div>

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
