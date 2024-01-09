from dataclasses import dataclass, field
from typing import List

from neurons.nodes.evm.ethereum.node import EthereumNode

@dataclass
class Block:
    block_number: int
    block_hash: str
    timestamp: int # Unix epoch time
    parent_hash: str
    nonce: int
    difficulty: int
    transactions: List["Transaction"] = field(default_factory=list)

@dataclass
class Transaction:
    block_hash: str
    block_number: int
    tx_hash: str
    timestamp: int # Unix epoch time
    gas_amount: int
    gas_price_wei: int
    from_address: str
    to_address: str
    value_wei: int
    is_internal: bool = False # transaction type is internal (smart contract execution) or not

class GraphCreator:
    def create_in_memory_graph_from_block(self, block_data):
        from dotenv import load_dotenv
        load_dotenv()

        block_number = int(block_data["number"])
        block_hash = block_data["hash"].hex()
        timestamp = int(block_data["timestamp"])
        parent_hash = block_data["parentHash"].hex()

        block = Block(
            block_number = block_number,
            block_hash = block_hash,
            timestamp = timestamp,
            parent_hash = parent_hash,
            nonce = block_data.get("nonce", 0),
            difficulty = block_data.get("totalDifficulty", 0)
        )

        ethereum_node = EthereumNode()
        
        for tx_hash in block_data["transactions"]:
            tx_data = ethereum_node.get_transaction_by_hash(tx_hash) # retrieve transaction details from transaction hash
            transaction = Transaction(
                block_hash = tx_data["blockHash"].hex(),
                block_number = tx_data["blockNumber"],
                tx_hash = tx_data["hash"].hex(),
                timestamp = tx_data.get("timestamp", timestamp),
                gas_amount = tx_data["gas"],
                gas_price_wei = int(tx_data.get("gasPrice", 0)),
                from_address = tx_data["from"],
                to_address = tx_data["to"],
                value_wei = int(tx_data.get("value", 0)),
                is_internal = False # for now, we assume only original transactions not smart contract executions.
            )
            block.transactions.append(transaction)
                
        return {"block": block}
