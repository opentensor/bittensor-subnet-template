from dataclasses import dataclass, field
from typing import List
from decimal import Decimal

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
class Account:
    address: str
    balance: Decimal
    timestamp: int # Unix epoch time

@dataclass
class Transaction:
    block_hash: str
    block_number: int
    tx_hash: str
    timestamp: int # Unix epoch time
    gas_amount: int
    gas_price_wei: int
    from_account: Account
    to_account: Account
    value_wei: Decimal
    symbol: str = "ETH" # ETH, USDT, USDC, ...


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
            
            from_address = tx_data["from"]
            from_address_balance = ethereum_node.get_balance_by_address(from_address)

            to_address = tx_data["to"]
            to_address_balance = ethereum_node.get_balance_by_address(to_address)

            from_account = Account(
                address = from_address,
                timestamp = timestamp,
                balance = from_address_balance
            )

            to_account = Account(
                address = to_address,
                timestamp = timestamp,
                balance = to_address_balance
            )

            transaction = Transaction(
                block_hash = tx_data["blockHash"].hex(),
                block_number = tx_data["blockNumber"],
                tx_hash = tx_data["hash"].hex(),
                timestamp = tx_data.get("timestamp", timestamp),
                gas_amount = int(tx_data.get("gas", 0)),
                gas_price_wei = int(tx_data.get("gasPrice", 0)),
                from_account = from_account,
                to_account = to_account,
                value_wei = int(tx_data.get("value", 0)),
                symbol = "ETH" # for now, we assume only original transactions not smart contract executions, so the symbol is "ETH"
            )
            block.transactions.append(transaction)
                
        return {"block": block}
