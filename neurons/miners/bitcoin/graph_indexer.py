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
                tx_id=tx_id, timestamp=tx_timestamp, fee_satoshi=fee_satoshi
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

    def get_latest_block_number(self):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (b:Block) RETURN MAX(b.height) AS latest_block_height"
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
                "CREATE INDEX ON :Block(height);",
                "CREATE INDEX ON :Transaction(tx_id);",
                "CREATE INDEX ON :Address(address)",
            ]
            for statement in index_creation_statements:
                try:
                    session.run(statement)
                except Exception as e:
                    print(f"An exception occurred: {e}")

    def create_graph_from_block(self, block):
        in_memory_graph = self.create_in_memory_graph_from_block(block)

        with self.driver.session() as session_initial:
            session = session_initial.begin_transaction()
            try:
                block_node = in_memory_graph["block"]
                previous_hash = (
                    block_node.previous_block_hash
                    if block_node.block_height > 1
                    else None
                )

                # Create the block node
                session.run(
                    """
                        CREATE (b:Block {
                            height: $block_height,
                            hash: $block_hash,
                            timestamp: $timestamp,
                            previous_hash: $previous_hash
                        })
                    """,
                    block_height=block_node.block_height,
                    block_hash=block_node.block_hash,
                    timestamp=block_node.timestamp,
                    previous_hash=previous_hash,
                )

                # Iterate over transactions in the block
                for tx in block_node.transactions:
                    session.run(
                        """
                            CREATE (t:Transaction {
                                tx_id: $tx_id,
                                fee_satoshi: $fee_satoshi,
                                timestamp: $timestamp
                            })
                            CREATE (b)-[:CONTAINS]->(t)
                        """,
                        tx_id=tx.tx_id,
                        fee_satoshi=tx.fee_satoshi,
                        timestamp=tx.timestamp,
                        block_hash=block_node.block_hash,
                    )

                    # Create VIN relationships
                    for vin in tx.vins:
                        session.run(
                            """
                                CREATE (v:VIN {
                                    vin_id: $vin_id,
                                    vout_id: $vout_id,
                                    script_sig: $script_sig,
                                    sequence: $sequence
                                })
                                CREATE (v)-[:IN]->(t)
                            """,
                            vin_id=vin.vin_id,
                            vout_id=vin.vout_id,
                            script_sig=vin.script_sig,
                            sequence=vin.sequence,
                            tx_id=tx.tx_id,
                        )

                    # Create VOUT relationships
                    for vout in tx.vouts:
                        session.run(
                            """
                                CREATE (v:VOUT {
                                    vout_id: $vout_id,
                                    value_satoshi: $value_satoshi,
                                    script_pub_key: $script_pub_key,
                                    is_spent: $is_spent,
                                    address: $address
                                })
                                CREATE (t)-[:OUT]->(v)
                                CREATE (a:Address {address: $address})
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

    from decimal import Decimal

    def create_graph_from_block2(self, block):
        with self.driver.session() as session_initial:
            session = session_initial.begin_transaction()
            try:
                block_height = block["height"]
                block_hash = block["hash"]
                block_previous_hash = block.get("previousblockhash", None)
                timestamp = block["time"]

                # Create the genesis block if it's the first one
                if block_height == 1:
                    session.run(
                        """
                        CREATE (b:Block {height: $block_height, hash: $block_hash, timestamp: $timestamp})
                        """,
                        block_height=block_height,
                        block_hash=block_hash,
                        timestamp=timestamp,
                    )
                else:
                    # Create a block node and link it to the previous block
                    block_previous_height = block_height - 1
                    session.run(
                        """
                        MATCH (prev:Block {height: $block_previous_height})
                        CREATE (b:Block {height: $block_height, hash: $block_hash, previous_hash: $block_previous_hash, timestamp: $timestamp})
                        MERGE (prev)-[:LINK]->(b)
                        """,
                        block_height=block_height,
                        block_hash=block_hash,
                        block_previous_height=block_previous_height,
                        block_previous_hash=block_previous_hash,
                        timestamp=timestamp,
                    )

                # Process transactions using UNWIND
                transactions = block["tx"]
                # First create all transaction nodes
                session.run(
                    """
                    UNWIND $transactions as tx
                    MATCH (b:Block {height: $block_height})
                    CREATE (t:Transaction {tx_id: tx.tx_id, block_height: $block_height, fee_satoshi: tx.fee_satoshi, size: tx.size, timestamp: $timestamp})
                    CREATE (b)-[:CONTAINS]->(t)
                    RETURN t.tx_id as tx_id, tx.vin as vins, tx.vout as vouts
                    """,
                    transactions=[
                        {
                            "tx_id": tx["txid"],
                            "fee_satoshi": int(
                                Decimal(tx.get("fee", 0)) * Decimal("100000000")
                            ),
                            "size": tx["size"],
                        }
                        for tx in transactions
                    ],
                    block_height=block_height,
                    timestamp=timestamp,
                )

                # Then process each transaction's vins and vouts
                for tx in transactions:
                    tx_id = tx["txid"]
                    vins = tx["vin"]
                    vouts = tx["vout"]

                    # Process vins
                    for vin in vins:
                        if "coinbase" in vin:
                            session.run(
                                """
                                MATCH (t:Transaction {tx_id: $tx_id})
                                CREATE (c:Coinbase {coinbase: $coinbase})
                                CREATE (c)-[:IN]->(t)
                                """,
                                tx_id=tx_id,
                                coinbase=vin["coinbase"],
                            )
                        else:
                            prev_tx_id = vin.get("txid")
                            prev_vout = vin.get("vout")
                            if prev_tx_id and prev_vout is not None:
                                session.run(
                                    """
                                    MATCH (t:Transaction {tx_id: $tx_id})
                                    MERGE (prev_tx:Transaction {tx_id: $prev_tx_id})
                                    MERGE (prev_output:Output {tx_id: $prev_tx_id, n: $prev_vout})
                                    MERGE (prev_output)-[:OUT]->(prev_tx)
                                    MERGE (prev_output)-[:IN]->(t)
                                    """,
                                    tx_id=tx_id,
                                    prev_tx_id=prev_tx_id,
                                    prev_vout=prev_vout,
                                )

                    # Process vouts
                    for vout in vouts:
                        value_satoshi = int(
                            Decimal(vout["value"]) * Decimal("100000000")
                        )
                        n = vout["n"]
                        scriptPubKey = vout["scriptPubKey"]
                        address = scriptPubKey.get("address", None)

                        session.run(
                            """
                            MATCH (t:Transaction {tx_id: $tx_id})
                            CREATE (out:Output {n: $n, value_satoshi: $value_satoshi, script_type: $script_type})
                            MERGE (t)-[:OUT]->(out)
                            """,
                            tx_id=tx_id,
                            n=n,
                            value_satoshi=value_satoshi,
                            script_type=scriptPubKey.get("type", "unknown"),
                        )

                        if address is not None:
                            session.run(
                                """
                                MATCH (out:Output {n: $n, tx_id: $tx_id})
                                MERGE (a:Address {address: $address})
                                MERGE (out)-[:LOCKED]->(a)
                                """,
                                tx_id=tx_id,
                                n=n,
                                address=address,
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
