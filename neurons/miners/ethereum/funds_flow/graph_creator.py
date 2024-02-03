from dataclasses import dataclass, field
from typing import List
from decimal import Decimal
import asyncio
from Crypto.Hash import SHA256

from web3.providers.base import JSONBaseProvider
from web3.providers import HTTPProvider
from web3 import Web3
from eth_abi import abi

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
    gas_used: int
    checksum: str # validation checksum for miner
    from_address: Account
    to_address: Account
    value_wei: Decimal
    symbol: str = "ETH" # ETH, USDT, USDC, ...


class GraphCreator:
    def create_in_memory_graph_from_block(self, block_data):
        from dotenv import load_dotenv
        load_dotenv()
        
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
        
        ethereum_node = EthereumNode()

        transactions = block_data["transactions"]
        loop = asyncio.get_event_loop()

        nativeTxResponses = loop.run_until_complete(ethereum_node.get_transaction(transactions))

        tokenTransactions = []

        for nativeResp in nativeTxResponses:
            nativeTx_data = nativeResp["result"]
            if 'from' in nativeTx_data and 'to' in nativeTx_data and 'value' in nativeTx_data and nativeTx_data["from"] != None and nativeTx_data["to"] != None:
                
                if int(nativeTx_data.get("value", 0), 0) > 0:

                    from_address = nativeTx_data["from"]
                    to_address = nativeTx_data["to"]

                    loop = asyncio.get_event_loop()
                    addresses = [from_address, to_address]
                    balance = loop.run_until_complete(ethereum_node.get_balance_by_addresses(addresses)) # wait till all address balance requests resolved

                    if nativeTx_data["from"] is None:
                        balance[0]["result"] = "0"
                    if nativeTx_data["to"] is None:
                        balance[1]["result"] = "0"

                    from_account = Account(
                        address = from_address,
                        timestamp = timestamp,
                        balance = int(balance[0]["result"], 0) # from_address_balance
                    )

                    to_account = Account(
                        address = to_address,
                        timestamp = timestamp,
                        balance = int(balance[1]["result"], 0) # to_address_balance
                    )

                    binary_address = nativeTx_data["hash"] + nativeTx_data["blockHash"] + nativeTx_data["from"] + nativeTx_data["to"]
                    checksum = sha256_result = SHA256.new(binary_address.encode('utf-8')).hexdigest()
                    
                    transaction = Transaction(
                        block_hash = nativeTx_data["blockHash"],
                        block_number = nativeTx_data["blockNumber"],
                        tx_hash = nativeTx_data["hash"],
                        timestamp = timestamp,
                        gas_used = int(nativeTx_data.get("gas", 0), 0) * int(nativeTx_data.get("gasPrice", 0), 0),
                        from_address = from_account,
                        to_address = to_account,
                        value_wei = int(nativeTx_data.get("value", 0), 0),
                        checksum = checksum,
                        symbol = "ETH" # for now, we assume only original transactions not smart contract executions, so the symbol is "ETH"
                    )


                    block.transactions.append(transaction)

                # Append native token transactions
                else:
                    tokenTransactions.append(nativeTx_data["hash"])
            else:
                tokenTransactions.append(nativeTx_data["hash"])

        tokenTypes = {}

        # token transactions
        if len(tokenTransactions) > 0:
            loop = asyncio.get_event_loop()
            rpcTxResponses = loop.run_until_complete(ethereum_node.get_transactionReceipt(tokenTransactions)) # wait till all tx details requests resolved

            for resp in rpcTxResponses:
                tx_data = resp["result"]
                # Transaction is token transfer
                if 'logs' in tx_data and len(tx_data["logs"]) > 0:
                    for log in tx_data["logs"]:
                        if len(log["topics"]) > 0:
                            try:
                                contractAddress = Web3.to_checksum_address(log["address"])
                                symbol = ''
                                if contractAddress not in tokenTypes:
                                    symbol = ethereum_node.get_symbol_name(contractAddress)
                                    if symbol == contractAddress:
                                        continue
                                    else:
                                        tokenTypes.update({contractAddress: symbol})
                                else:
                                    symbol = tokenTypes[contractAddress]

                                from_address = abi.decode(['address'], bytes.fromhex(log["topics"][1][2:]))
                                to_address = abi.decode(['address'], bytes.fromhex(log["topics"][2][2:]))
                                from_address = ''.join(from_address)
                                to_address = ''.join(to_address)

                                if from_address is None:
                                    continue
                                if to_address is None:
                                    continue

                                loop = asyncio.get_event_loop()
                                addresses = [from_address, to_address]
                                balance = loop.run_until_complete(ethereum_node.get_balance_by_addresses(addresses)) # wait till all address balance requests resolved

                                from_account = Account(
                                    address = from_address,
                                    timestamp = timestamp,
                                    balance = balance[0]["result"] # from_address_balance
                                )

                                to_account = Account(
                                    address = to_address,
                                    timestamp = timestamp,
                                    balance = balance[1]["result"] # to_address_balance
                                )

                                value = abi.decode(['uint256'], bytes.fromhex(log["data"][2:]));

                                binary_address = tx_data["transactionHash"] + tx_data["blockHash"] + from_address + to_address
                                checksum = sha256_result = SHA256.new(binary_address.encode('utf-8')).hexdigest()

                                transaction = Transaction(
                                    block_hash = tx_data["blockHash"],
                                    block_number = tx_data["blockNumber"],
                                    tx_hash = tx_data["transactionHash"],
                                    gas_used = int(tx_data.get("gasUsed", 0), 0),
                                    from_address = from_account,
                                    to_address = to_account,
                                    timestamp = timestamp,
                                    value_wei = int(''.join(map(str, value))),
                                    checksum = checksum,
                                    symbol = symbol
                                )

                                block.transactions.append(transaction)
                                
                            except:
                                continue

        return {"block": block}
