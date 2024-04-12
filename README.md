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
