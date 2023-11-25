from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal, getcontext

from neurons.nodes.bitcoin.node_utils import (
    pubkey_to_address,
    construct_redeem_script,
    hash_redeem_script,
    create_p2sh_address,
)


@dataclass
class Block:
    block_height: int
    block_hash: str
    timestamp: int  # Using int to represent Unix epoch time
    previous_block_hash: str
    nonce: int
    difficulty: int
    transactions: List["Transaction"] = field(default_factory=list)


@dataclass
class Transaction:
    tx_id: str
    block_height: int
    timestamp: int  # Using int to represent Unix epoch time
    fee_satoshi: int
    vins: List["VIN"] = field(default_factory=list)
    vouts: List["VOUT"] = field(default_factory=list)
    is_coinbase: bool = False


@dataclass
class VOUT:
    vout_id: int
    value_satoshi: int
    script_pub_key: Optional[str]
    is_spent: bool
    address: str


@dataclass
class VIN:
    vin_id: int
    vout_id: int
    script_sig: Optional[str]
    sequence: Optional[int]


getcontext().prec = 28
SATOSHI = Decimal("100000000")


class GraphCreator:
    def create_in_memory_graph_from_block(self, block_data):
        block_height = block_data["height"]
        block_hash = block_data["hash"]
        block_previous_hash = block_data.get("previousblockhash", "")
        timestamp = int(block_data["time"])

        block = Block(
            block_height=block_height,
            block_hash=block_hash,
            timestamp=timestamp,
            previous_block_hash=block_previous_hash,
            nonce=block_data.get("nonce", 0),
            difficulty=block_data.get("difficulty", 0),
        )

        for tx_data in block_data["tx"]:
            tx_id = tx_data["txid"]
            fee = Decimal(tx_data.get("fee", 0))
            fee_satoshi = int(fee * SATOSHI)
            tx_timestamp = int(tx_data.get("time", timestamp))

            tx = Transaction(
                tx_id=tx_id,
                block_height=block_height,
                timestamp=tx_timestamp,
                fee_satoshi=fee_satoshi,
            )

            for vin_data in tx_data["vin"]:
                vin = VIN(
                    vin_id=vin_data.get("sequence", 0),
                    vout_id=vin_data.get("vout", 0),
                    script_sig=vin_data.get("scriptSig", {}).get("asm", ""),
                    sequence=vin_data.get("sequence", 0),
                )
                tx.vins.append(vin)
                tx.is_coinbase = "coinbase" in vin_data

            for vout_data in tx_data["vout"]:
                script_type = vout_data["scriptPubKey"].get("type", "")
                if "nonstandard" in script_type or script_type == "nulldata":
                    continue

                value_satoshi = int(Decimal(vout_data["value"]) * SATOSHI)
                n = vout_data["n"]
                script_pub_key_asm = vout_data["scriptPubKey"].get("asm", "")

                address = vout_data["scriptPubKey"].get("address", "")
                if not address:
                    addresses = vout_data["scriptPubKey"].get("addresses", [])
                    if addresses:
                        address = addresses[0]
                    elif "OP_CHECKSIG" in script_pub_key_asm:
                        pubkey = script_pub_key_asm.split()[0]
                        address = pubkey_to_address(pubkey)
                    elif "OP_CHECKMULTISIG" in script_pub_key_asm:
                        pubkeys = script_pub_key_asm.split()[1:-2]
                        m = int(script_pub_key_asm.split()[0])
                        redeem_script = construct_redeem_script(pubkeys, m)
                        hashed_script = hash_redeem_script(redeem_script)
                        address = create_p2sh_address(hashed_script)
                    else:
                        raise Exception(
                            f"Unknown address type: {vout_data['scriptPubKey']}"
                        )

                vout = VOUT(
                    vout_id=n,
                    value_satoshi=value_satoshi,
                    script_pub_key=script_pub_key_asm,
                    is_spent=False,
                    address=address,
                )
                tx.vouts.append(vout)

            block.transactions.append(tx)

        return {"block": block}
