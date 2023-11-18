# The Blockchain Insights Subnet - High Level Architecture

## System Context


<img src="docs/imgs/hla_system_context.png" alt="System Context Diagram" title="System Context Diagram" height="380" />

### MINERS
- Different types of miners optimized for specific blockchains or operations like Bitcoin mining, Ethereum mining, or DeFi applications.

### PROTOCOL
- The set of rules or communication protocol governing interactions between miners and the validator.

### Subnets
- Subsets of the main blockchain network or sidechains with their own rules, specialized for specific functions.

### Query Studio
- Interface for querying and interacting with blockchain data, as mentioned in the container context.

### Users
- End-users or clients interacting with the blockchain network, possibly through interfaces like the Query Studio.
- 
## Container Diagram

<img src="docs/imgs/hla_container_context.png" alt="Container Diagram" title="Container Diagram" height="320" />

### Blockchain Node
- Maintains a copy of the blockchain, processes transactions, and participates in consensus mechanisms.

### Indexer
- Reads data from the blockchain node and organizes it into a searchable and optimized format for complex queries.

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