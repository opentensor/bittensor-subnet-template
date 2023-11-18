# The Blockchain Insights Subnet - High Level Architecture

## System Context


<img src="docs/imgs/hla_system_context.png" alt="System Context Diagram" title="System Context Diagram" height="380" />

### MINERS
- Miners in the Blockchain Insights subnet are tasked with the crucial job of transforming raw blockchain data into structured graph models. These models are not limited to simple transactions; they extend to encompass DeFi protocol transactions and NFT exchanges, providing a comprehensive view of asset flow. The funds flow graph model is a prime example of their work, offering a detailed visualization of monetary movements between various addresses or accounts. Through these models, miners enable the network to map and scrutinize the complex web of blockchain interactions.

### PROTOCOL
- The protocol is a defined set of rules for data exchange between miners and validators in the Blockchain Insights subnet. It governs how miners serve data in response to queries from validators, APIs, or other subnets. This protocol delineates the data contract, specifying the structure and format of data to be exchanged, ensuring consistency and interoperability within the network's operations.

### Validators
- Within the blockchain insights subnet, validators perform a crucial, multifaceted role. They act as a proxy, efficiently routing queries between miners, other subnets, and APIs. In addition to this intermediary function, validators are responsible for grouping miners. This grouping is based on the specific blockchain domains and graph model types that the miners specialize in, optimizing the subnet's query handling capabilities. Moreover, validators rank these miners, taking into account the correctness and performance of the data they provide. This ranking ensures that the subnet maintains high standards of data quality and performance, thereby upholding the overall integrity and reliability of the blockchain insights generated.

### Subnets
- Subnets are distinct segments of the Bittensor network, each able to query and interact with the blockchain insights subnet for specific data and analytical purposes.

### Query Studio
- Query Studio is a user-friendly application in the Blockchain Insights subnet for executing data analytics queries and visualizing results.

### Users
- End-users or clients interacting with the Blockchain Insights subnet, through interfaces like the Query Studio or API.

## Container Diagram

<img src="docs/imgs/hla_container_context.png" alt="Container Diagram" title="Container Diagram" height="320" />

### Blockchain Node
- Maintains a copy of the blockchain, processes transactions, and participates in consensus mechanisms.

### Indexer
- The Indexer is a component that processes blockchain data, converting it into graph-based models for enhanced query capabilities. It serves as a bridge between raw data and structured insights, enabling complex data analysis within the blockchain insights subnet.

### Graph Model
- A data store optimized for graph-based storage and querying, representing blockchain entities and their relationships.

### Miner
- Performs mining processes, including transaction validation, block creation, and maintaining network consensus.

### Miner's Registry
- Tracks miners' identities, resources, and metrics of performance or trustworthiness.

### Validator
- Checks the validity of transactions or blocks, playing a crucial role in the consensus mechanism.

### API
- Provides programmatic access to blockchain data and operations for applications.

### Blockchain API
- Might be an external service like Blockchair offering standardized API access to various blockchain networks.

### Query Studio
- A user interface for constructing and running queries against blockchain data, with possible visualization tools.