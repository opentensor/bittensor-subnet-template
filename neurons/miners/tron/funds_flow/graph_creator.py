from dataclasses import dataclass, field
from typing import List
from Crypto.Hash import SHA256

from neurons.nodes.tron.node import TronNode

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
    balance: str
    timestamp: int # Unix epoch time

@dataclass
class Transaction:
    block_hash: str
    block_number: int
    tx_hash: str
    timestamp: int # Unix epoch time
    checksum: str # validation checksum for miner
    from_address: Account
    to_address: Account
    value_sun: str
    symbol: str = "TRX" # USDT, USDC, ...


class GraphCreator:
    def __init__(self):
        self.tokenTypes = {}

    def create_in_memory_graph_from_block(self, tron_node, block_data):
        
        from dotenv import load_dotenv
        load_dotenv()

        addresses = []
        block_number = int(block_data["number"])
        block_hash = "".join(["{:02X}".format(b) for b in block_data["hash"]])
        timestamp = int(block_data["timestamp"])
        parent_hash = "".join(["{:02X}".format(b) for b in block_data["parentHash"]])

        block = Block(
            block_number = block_number,
            block_hash = block_hash,
            timestamp = timestamp,
            parent_hash = parent_hash,
            nonce = block_data.get("nonce", 0),
            difficulty = block_data.get("totalDifficulty", 0)
        )

        transactions = block_data["transactions"]

        txData = tron_node.get_transaction(transactions)

        for tx in txData:
            txType = tx["raw_data"]["contract"][0]["type"]
            if 'txID' in tx and txType == "TransferContract":
                value = tx["raw_data"]["contract"][0]["parameter"]
                from_address = value["owner_address"]
                to_address = value["to_address"]

                from_balance = tron_node.get_account_balance(from_address)
                to_balance = tron_node.get_account_balance(to_address)

                from_account = Account(
                    address = from_address,
                    timestamp = timestamp,
                    balance = str(from_balance)
                )

                to_account = Account(
                    address = to_address,
                    timestamp = timestamp,
                    balance = str(to_balance)
                )

                binary_address = tx["txID"] + tx["blockID"] + from_address + to_address
                checksum = SHA256.new(binary_address.encode('utf-8')).hexdigest()
                
                transaction = Transaction(
                    block_hash = tx["blockID"],
                    block_number = int(tx["blockNumber"], 0),
                    tx_hash = tx["txID"],
                    timestamp = timestamp,
                    from_address = from_account,
                    to_address = to_account,
                    value_sun = str(int(value.get("amount", 0), 0)),
                    checksum = checksum,
                    symbol = "TRX" # for now, we assume only original transactions not smart contract executions, so the symbol is "ETH"
                )

                addresses.append(from_address)
                addresses.append(to_address)
                block.transactions.append(transaction)

        return {"block": block}
