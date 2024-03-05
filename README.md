<div align="center">

# **Bittensor Blockchain Insights Subnet** <!-- omit in toc -->
<img src="docs/imgs/logo.png" alt="Logo" title="Logo" height="256"  />

[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

---

## Unlocking the Power of Blockchain Data <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Subnet](https://taostats.io/subnets/netuid-15/) • [Research](https://bittensor.com/whitepaper)
</div>

### Table of Contents <!-- omit in toc -->
- [Overview](#Blockchain-insights-overview)
- [Instalation & Configuration](#instalation)
- [Development Roadmap](#Project-roadmap)
- [High Level Architecture](#High-level-architecture)
- [License](#license)
---

## Blockchain Insights Overview
Blockchain Insights Subnet is an innovative project focusing on transforming raw blockchain data into structured graph models. This project aims to provide comprehensive insights into various blockchain activities, including simple transactions, DeFi protocol transactions, and NFT exchanges.

### Features
- **Data Analytics:**
  - **Desktop Application:** Enables data analytics queries and result visualization.
    - **Native Tokens and ERC-20 Token Insights:** Provides analysis for native tokens and ERC-20 token transactions.
    - **DeFi and NFT Insights:** Provides analysis for decentralized finance and non-fungible token transactions.
    - **Customizable Queries:** Allows users to execute tailored queries for specific data analysis needs.
  - **API Support:**
    - **Predefined Queries:** Offers a set of standard queries for common analytics tasks.
    - **Cypher Endpoint:** Enables custom query execution for advanced data analysis.
- **Graph Model Transformation:**
  - **Funds Flow Graph Model:** Visualizes monetary movements between addresses or accounts.
  - **Extensible Graph Model:** Allows adding new models to support diverse data analysis needs.
- **Blockchain Support:**
  - **Bitcoin-like UTXO Blockchains:** Integration with Bitcoin and other UTXO-based blockchains (etc. Bitcoin, Litecoin, Dogecoin and more).
  - **Ethereum and EVM-Compatible Blockchains:** Compatibility with Ethereum, including Layer 2 solutions (etc. Ethereum, Avax, Polygon, Arbitrum and more).
---
## Instalation
Instalation files and instructions can be found in the [blockchain data subnet ops](https://github.com/blockchain-insights/blockchain-data-subnet-ops) repository.

## Project Roadmap
Development of the Blockchain Insights Subnet is divided into four streams, each with its own objectives and milestones. These streams are:
- **[BI]** Blockchain Integrations
- **[AI]** Intelligence
- **[QS]** Query Studio
- **[UE]** User Experience

The following sections outline the objectives and milestones for each stream.
- **Milestone 0**
  - [BI] Launch the subnet with a support for the Bitcoin blockchain.
  - [AI] Develop and integrate the funds flow graph model for Bitcoin data analysis.
- **Milestone 1**
  - [BI] Add DOGE blockchain support.
  - [AI] Refine validator scoring and weighting mechanisms.
  - [QS] Launch a basic public API for Query Studio.
  - [UE] Enhance documentation and upgrade infrastructure.
- **Milestone 2**
  - [BI] Integrate LTC blockchain support.
  - [QS] Extend Query Studio's public API functionalities.
  - [HR] Grow the team and introduce bounties for key feature development.
  - [UE] Further refine documentation and infrastructure.
- **Next Milestones**
  - TBA

## High Level Architecture
Description of the Blockchain Insights Subnet's high-level architecture, including the system context and container diagrams.

### System Context
<img src="docs/imgs/hla_system_context.png" alt="System Context Diagram" title="System Context Diagram" height="380" />

#### MINERS
- Miners in the Blockchain Insights subnet are tasked with the crucial job of transforming raw blockchain data into structured graph models. These models are not limited to simple transactions; they extend to encompass DeFi protocol transactions and NFT exchanges, providing a comprehensive view of asset flow. The funds flow graph model is a prime example of their work, offering a detailed visualization of monetary movements between various addresses or accounts. Through these models, miners enable the network to map and scrutinize the complex web of blockchain interactions.

#### PROTOCOL
- The protocol is a defined set of rules for data exchange between miners and validators in the Blockchain Insights subnet. It governs how miners serve data in response to queries from validators, APIs, or other subnets. This protocol delineates the data contract, specifying the structure and format of data to be exchanged, ensuring consistency and interoperability within the network's operations.

#### Validators
- Within the blockchain insights subnet, validators perform a crucial, multifaceted role. They act as a proxy, efficiently routing queries between miners, other subnets, and APIs. In addition to this intermediary function, validators are responsible for grouping miners. This grouping is based on the specific blockchain domains and graph model types that the miners specialize in, optimizing the subnet's query handling capabilities. Moreover, validators rank these miners, taking into account the correctness and performance of the data they provide. This ranking ensures that the subnet maintains high standards of data quality and performance, thereby upholding the overall integrity and reliability of the blockchain insights generated.

#### Subnets
- Subnets are distinct segments of the Bittensor network, each able to query and interact with the blockchain insights subnet for specific data and analytical purposes.

#### Query Studio
- Query Studio is a user-friendly application in the Blockchain Insights subnet for executing data analytics queries and visualizing results.

#### Users
- End-users or clients interacting with the Blockchain Insights subnet, through interfaces like the Query Studio or API.

### Container Diagram

<img src="docs/imgs/hla_container_context.png" alt="Container Diagram" title="Container Diagram" height="320" />

#### Blockchain Node
- Maintains a copy of the blockchain, processes transactions, and participates in consensus mechanisms.

#### Indexer
- The Indexer is a component that processes blockchain data, converting it into graph-based models for enhanced query capabilities. It serves as a bridge between raw data and structured insights, enabling complex data analysis within the blockchain insights subnet.

#### Graph Model - Memgraph and MAGE
- The Graph Model in the blockchain insights subnet leverages Memgraph, an in-memory graph database that supports the creation of snapshots on disk. This enables the execution of Cypher queries, which are used to interrogate the graph database, allowing for complex data relationship analysis and insights.
- Memgraph Advanced Graph Extensions, or MAGE, is a vital addition to this system. It is an open-source library of graph algorithms that aims to become a leading solution in the field by providing a user-friendly interface across multiple programming languages​​. MAGE facilitates the extension of graph database functionalities, enabling users to quickly implement a wide range of graph algorithms essential for advanced analytics​​.
- Furthermore, MAGE can leverage the GPU for accelerated execution of graph algorithms when used with the Memgraph X NVIDIA cuGraph version of the library, which enhances performance significantly, especially for large-scale graph analytics​​. This feature is particularly relevant for operations that require intensive computation, like those needed for analyzing blockchain data.
- By integrating MAGE, the blockchain insights subnet can benefit from the shared innovations of developers through custom Cypher procedures, which enrich the community's analytical capabilities​​. The use of NVIDIA GPU support with Memgraph makes it a robust solution for processing and analyzing real-time data streams in the blockchain insights subnet, ensuring fast and efficient data handling.

#### Miner
- Serves as the data provider to validators through a predefined PROTOCOL. Miners can be of various types, differentiated by the specific blockchain they support and the graph model types they employ. This versatility allows Miners to handle a diverse range of data requests, catering to the unique requirements of different blockchain networks and analytics demands. By aligning their capabilities with the graph models, Miners ensure that validators have access to the precise data needed, facilitating accurate and efficient data validation and analysis within the blockchain insights subnet.

#### PROTOCOL 
- The protocol within the blockchain insights subnet is a set of rules facilitating data exchange between miners and validators. It allows miners to serve data in response to queries originating from validators, APIs, or other subnets. This protocol outlines the specific data contract, which includes the structure and format of the data to be exchanged, ensuring consistency and effective communication within the network. The protocol's design is crucial for maintaining the integrity and efficiency of data transfer in the subnet.

#### Validator
- Within the blockchain insights subnet, the role of the validator is multifaceted. Validators act as a routing layer, directing queries between the API, subnets, and miners. They are responsible for organizing miners into groups based on their area of blockchain specialization and the types of graph models they handle. Additionally, validators rank miners by the accuracy and performance of their data contributions. This ranking is key to maintaining the subnet's standard for data quality and efficiency, ensuring the reliability of the insights provided. Through these activities, validators uphold the subnet's data integrity and streamline the flow of information.

#### Miner's Registry
- The Miner's Registry is a database residing on the validator's side within the blockchain insights subnet. Its primary function is to keep track of the various miners, organizing them by the specific blockchain networks they support and the graph models they are capable of handling. This organization enables validators to efficiently manage and allocate data requests to the appropriate miners based on their specialties, ensuring that the data served is relevant and up to the validators' requirements for accuracy and performance. The Miner's Registry is a critical component in maintaining the integrity of the subnet's operations, enabling a structured and systematic approach to handling the flow of blockchain data.

#### Blockchair API
- The Blockchair API is a search and analytics engine that provides access to data across 17 blockchains, supporting complex queries for detailed analysis. It is used within the blockchain insights subnet to validate miner outputs, ensuring data accuracy and integrity.

#### API
- The API in the blockchain insights subnet serves as a gateway for executing Cypher queries on the data provided by miners. Requests made through the API are routed by the validator to the appropriate miners based on their registered capabilities in the Miner's Registry. This ensures that queries are handled efficiently and by the most suitable data source. The API offers a range of predefined queries for common tasks and analytics, as well as a Cypher endpoint that allows users to execute custom queries. This dual functionality facilitates both standard and bespoke data analysis, making the API a versatile tool for accessing and interrogating the wealth of information within the subnet.

#### SUBNETS
- In the blockchain insights subnet, subnets represent interconnected segments of the broader Bittensor network. Each subnet has the capability to query the blockchain insights subnet for specific data and insights. These subnets facilitate specialized interactions and data exchanges within the network, allowing for targeted analytics and information retrieval tailored to their unique requirements.

#### Query Studio
- Query Studio is a WPF (Windows Presentation Foundation) analytical application designed for end users to perform queries against the data served by miners. It provides a user interface that allows for the execution of complex queries, facilitating the analysis and visualization of blockchain data directly on the Windows platform.
---

## Writing your own incentive mechanism

As described in [Quickstarter template](#quickstarter-template) section above, when you are ready to write your own incentive mechanism, update this template repository by editing the following files. The code in these files contains detailed documentation on how to update the template. Read the documentation in each of the files to understand how to update the template. There are multiple **TODO**s in each of the files identifying sections you should update. These files are:
- `template/protocol.py`: Contains the definition of the wire-protocol used by miners and validators.
- `neurons/miner.py`: Script that defines the miner's behavior, i.e., how the miner responds to requests from validators.
- `neurons/validator.py`: This script defines the validator's behavior, i.e., how the validator requests information from the miners and determines the scores.
- `template/forward.py`: Contains the definition of the validator's forward pass.
- `template/reward.py`: Contains the definition of how validators reward miner responses.

In addition to the above files, you should also update the following files:
- `README.md`: This file contains the documentation for your project. Update this file to reflect your project's documentation.
- `CONTRIBUTING.md`: This file contains the instructions for contributing to your project. Update this file to reflect your project's contribution guidelines.
- `template/__init__.py`: This file contains the version of your project.
- `setup.py`: This file contains the metadata about your project. Update this file to reflect your project's metadata.
- `docs/`: This directory contains the documentation for your project. Update this directory to reflect your project's documentation.

__Note__
The `template` directory should also be renamed to your project name.
---

# Writing your own subnet API
To leverage the abstract `SubnetsAPI` in Bittensor, you can implement a standardized interface. This interface is used to interact with the Bittensor network and can is used by a client to interact with the subnet through its exposed axons.

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
        Prepare the synapse-specific payload.
        """
        ...

    @abstractmethod
    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> Any:
        """
        Process the responses from the network.
        """
        ...

```


Here is a toy example:

```python
from bittensor.subnets import SubnetsAPI
from MySubnet import MySynapse

class MySynapseAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 99

    def prepare_synapse(self, prompt: str) -> MySynapse:
        # Do any preparatory work to fill the synapse
        data = do_prompt_injection(prompt)

        # Fill the synapse for transit
        synapse = StoreUser(
            messages=[data],
        )
        # Send it along
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> str:
        # Look through the responses for information required by your application
        for response in responses:
            if response.dendrite.status_code != 200:
                continue
            # potentially apply post processing
            result_data = postprocess_data_from_response(response)
        # return data to the client
        return result_data
```

You can use a subnet API to the registry by doing the following:
1. Download and install the specific repo you want
1. Import the appropriate API handler from bespoke subnets
1. Make the query given the subnet specific API


See a simplified example for subnet 21 (`FileTao` storage) below. See `examples/subnet21.py` file for a full implementation example to follow:

```python

# Subnet 21 Interface Example

class StoreUserAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(
        self,
        data: bytes,
        encrypt=False,
        ttl=60 * 60 * 24 * 30,
        encoding="utf-8",
    ) -> StoreUser:
        data = bytes(data, encoding) if isinstance(data, str) else data
        encrypted_data, encryption_payload = (
            encrypt_data(data, self.wallet) if encrypt else (data, "{}")
        )
        expected_cid = generate_cid_string(encrypted_data)
        encoded_data = base64.b64encode(encrypted_data)

        synapse = StoreUser(
            encrypted_data=encoded_data,
            encryption_payload=encryption_payload,
            ttl=ttl,
        )

        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> str:
        for response in responses:
            if response.dendrite.status_code != 200:
                continue
            stored_cid = (
                response.data_hash.decode("utf-8")
                if isinstance(response.data_hash, bytes)
                else response.data_hash
            )
            bt.logging.debug("received data CID: {}".format(stored_cid))
            break

        return stored_cid


class RetrieveUserAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(self, cid: str) -> RetrieveUser:
        synapse = RetrieveUser(data_hash=cid)
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> bytes:
        success = False
        decrypted_data = b""
        for response in responses:
            if response.dendrite.status_code != 200:
                continue
            decrypted_data = decrypt_data_with_private_key(
                encrypted_data,
                response.encryption_payload,
                bytes(self.wallet.coldkey.private_key.hex(), "utf-8"),
            )
        return data

 
Example usage of the `FileTao` interface, which can serve as an example for other subnets.

# import the bespoke subnet API
from storage import StoreUserAPI, RetrieveUserAPI

wallet = bt.wallet(wallet="default", hotkey="default") # the wallet used for querying
metagraph = bt.metagraph(netuid=21)  # metagraph of the subnet desired
query_axons = metagraph.axons... # define custom logic to retrieve desired axons (e.g. validator set, specific miners, etc)

# Store the data on subnet 21
bt.logging.info(f"Initiating store_handler: {store_handler}")
cid = await StoreUserAPI(
      axons=query_axons, # the axons you wish to query
      # Below: Parameters passed to `prepare_synapse` for this API subclass
      data=b"Hello Bittensor!",
      encrypt=False,
      ttl=60 * 60 * 24 * 30, 
      encoding="utf-8",
      uid=None,
)
# The Content Identifier that corresponds to the stored data
print(cid)
> "bafkreifv6hp4o6bllj2nkdtzbq6uh7iia6bgqgd3aallvfhagym2s757v4

# Now retrieve data from SN21 (storage)
data = await RetrieveUserAPI(
  axons=query_axons, # axons desired to query
  cid=cid, # the content identifier to fetch the data
)
print(data)
> b"Hello Bittensor!"
```


# Subnet Links
In order to see real-world examples of subnets in-action, see the `subnet_links.py` document or access them from inside the `template` package by:
```python
import template
template.SUBNET_LINKS
[{'name': 'sn0', 'url': ''},
 {'name': 'sn1', 'url': 'https://github.com/opentensor/text-prompting/'},
 {'name': 'sn2', 'url': 'https://github.com/bittranslateio/bittranslate/'},
 {'name': 'sn3', 'url': 'https://github.com/gitphantomman/scraping_subnet/'},
 {'name': 'sn4', 'url': 'https://github.com/manifold-inc/targon/'},
...
]
```

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
