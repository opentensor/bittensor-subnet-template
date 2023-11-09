from neo4j import GraphDatabase
from neo4j import Transaction
from neurons.miners.bitcoin.configs import GraphIndexerConfig
from decimal import Decimal, getcontext
from neo4j import GraphDatabase
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from typing import Optional, List

getcontext().prec = 28


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


class GraphIndexer:
    def __init__(self, config: GraphIndexerConfig):
        self.driver = GraphDatabase.driver(
            config.graph_db_url,
            auth=(config.graph_db_user, config.graph_db_password),
        )

    def close(self):
        self.driver.close()

    def get_latest_block_number(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Transaction)
                RETURN MAX(t.block_height) AS latest_block_height
                """
            )
            single_result = result.single()
            if single_result[0] is None:
                return 0
            return single_result[0]

    from decimal import Decimal, getcontext

    # Set the precision high enough to handle satoshis for Bitcoin transactions
    getcontext().prec = 28

    from neo4j import Transaction

    def create_indexes(self):
        with self.driver.session() as session:
            index_creation_statements = [
                "CREATE INDEX ON :Transaction(tx_id);",
                "CREATE INDEX ON :Transaction(block_height);",
            ]
            for statement in index_creation_statements:
                try:
                    session.run(statement)
                except Exception as e:
                    print(f"An exception occurred: {e}")

    def create_in_memory_graph_from_block(self, block_data):
        # Parse block data
        block_height = block_data["height"]
        block_hash = block_data["hash"]
        block_previous_hash = block_data.get("previousblockhash", "")
        timestamp = int(block_data["time"])  # Converting to Unix epoch time

        # Create the Block instance
        block = Block(
            block_height=block_height,
            block_hash=block_hash,
            timestamp=timestamp,
            previous_block_hash=block_previous_hash,
            nonce=block_data.get("nonce", 0),
            difficulty=block_data.get("difficulty", 0),
        )

        # Parse transactions
        for tx_data in block_data["tx"]:
            tx_id = tx_data["txid"]
            fee = Decimal(tx_data.get("fee", 0))
            fee_satoshi = int(fee * Decimal("100000000"))
            tx_timestamp = int(
                tx_data.get("time", block_data["time"])
            )  # Fallback to block timestamp

            # Create the Transaction instance
            tx = Transaction(
                tx_id=tx_id,
                timestamp=tx_timestamp,
                fee_satoshi=fee_satoshi,
                block_height=block_height,
            )

            # Parse VINs
            for vin_data in tx_data["vin"]:
                vin = VIN(
                    vin_id=vin_data.get(
                        "sequence", 0
                    ),  # Assuming sequence can serve as a unique ID
                    vout_id=vin_data.get("vout", 0),
                    script_sig=vin_data.get("scriptSig", {}).get("asm", ""),
                    sequence=vin_data.get("sequence", 0),
                )
                tx.vins.append(vin)

            # Parse VOUTs
            for vout_data in tx_data["vout"]:
                value_satoshi = int(Decimal(vout_data["value"]) * Decimal("100000000"))
                n = vout_data["n"]
                script_pub_key = vout_data["scriptPubKey"].get("hex", "")
                addresses = vout_data["scriptPubKey"].get("addresses", [""])
                address = addresses[0] if addresses else ""

                vout = VOUT(
                    vout_id=n,
                    value_satoshi=value_satoshi,
                    script_pub_key=script_pub_key,
                    is_spent=False,  # Default value; would need additional logic to determine
                    address=address,
                )
                tx.vouts.append(vout)

            # Add the transaction to the block
            block.transactions.append(tx)

        return {"block": block}

    def create_graph_from_block(self, block):
        in_memory_graph = self.create_in_memory_graph_from_block(block)

        with self.driver.session() as session_initial:
            session = session_initial.begin_transaction()
            try:
                block_node = in_memory_graph["block"]

                for tx in block_node.transactions:
                    is_coinbase = (
                        tx.is_coinbase if hasattr(tx, "is_coinbase") else False
                    )

                    session.run(
                        """
                            CREATE (t:Transaction {
                                block_height: $block_height,
                                block_hash: $block_hash,
                                block_timestamp: $block_timestamp,
                                tx_id: $tx_id,
                                timestamp: $timestamp,
                                is_coinbase: $is_coinbase,
                                fee_satoshi: $fee_satoshi
                            })
                        """,
                        block_height=block_node.block_height,
                        block_hash=block_node.block_hash,
                        block_timestamp=block_node.timestamp,
                        tx_id=tx.tx_id,
                        timestamp=tx.timestamp,
                        is_coinbase=is_coinbase,
                        fee_satoshi=tx.fee_satoshi if not is_coinbase else 0,
                    )

                    # If it's a coinbase transaction, create an Output with special attributes
                    if is_coinbase:
                        session.run(
                            """
                                MATCH (t:Transaction {tx_id: $tx_id})
                                CREATE (v:Output {
                                    vout_id: $vout_id,
                                    value_satoshi: $value_satoshi,
                                    script_pub_key: $script_pub_key,
                                    is_coinbase: $is_coinbase
                                })
                                CREATE (t)-[:OUT]->(v)
                                CREATE (a:Address {address: $address})
                                CREATE (v)-[:LOCKED]->(a)
                            """,
                            vout_id=tx.vout_id,  # The ID for the coinbase output, often 0 or a special identifier
                            value_satoshi=tx.value_satoshi,  # The block reward plus any transaction fees from other transactions
                            script_pub_key=tx.script_pub_key,  # Often contains arbitrary data or even messages
                            tx_id=tx.tx_id,
                            address=tx.address,  # The address of the miner receiving the block reward
                            is_coinbase=is_coinbase,
                        )

                    # Create VIN relationships
                    for vin in tx.vins:
                        session.run(
                            """
                                MATCH (v:Output {vout_id: $vout_id})
                                MATCH (t:Transaction {tx_id: $tx_id})
                                CREATE (v)-[:IN {
                                    vin_id: $vin_id,
                                    vout_id: $vout_id
                                }]->(t)
                            """,
                            vout_id=vin.vout_id,
                            vin_id=vin.vin_id,
                            tx_id=tx.tx_id,
                        )

                    # Create VOUT relationships
                    for vout in tx.vouts:
                        session.run(
                            """
                                CREATE (v:Output {
                                    vout_id: $vout_id,
                                    value_satoshi: $value_satoshi,
                                    script_pub_key: $script_pub_key,
                                    is_spent: $is_spent
                                })
                                CREATE (a:Address {address: $address})
                                CREATE (t:Transaction {tx_id: $tx_id})
                                CREATE (t)-[:OUT]->(v)
                                CREATE (v)-[:LOCKED]->(a)
                            """,
                            vout_id=vout.vout_id,
                            value_satoshi=vout.value_satoshi,
                            script_pub_key=vout.script_pub_key,
                            is_spent=vout.is_spent,
                            address=vout.address if vout.address else "",
                            tx_id=tx.tx_id,
                        )

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"An exception occurred: {e}")
                return False
            finally:
                if not session.closed():
                    session.close()
