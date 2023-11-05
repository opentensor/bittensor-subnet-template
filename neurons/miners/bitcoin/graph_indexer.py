from neo4j import GraphDatabase
from neo4j import Transaction
from neurons.miners.bitcoin.configs import GraphIndexerConfig
from decimal import Decimal, getcontext

getcontext().prec = 28


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

    def create_graph_from_block_original(self, block):
        with self.driver.session() as session_initial:
            session = session_initial.begin_transaction()
            try:
                block_height = block["height"]
                block_hash = block["hash"]
                block_previous_hash = block["previousblockhash"]
                timestamp = block["time"]

                if block_height == 1:
                    # Create the genesis block
                    session.run(
                        """
                            CREATE (b:Block {height: $block_height, hash: $block_hash, timestamp: $timestamp})
                            """,
                        block_height=block_height,
                        block_hash=block_hash,
                        timestamp=timestamp,
                    )
                else:
                    # Create a block node
                    block_previous_height = block_height - 1
                    session.run(
                        """
                            MATCH (prev:Block {height: $block_previous_height})
                            CREATE (b:Block {height: $block_height, hash: $block_hash, previous_hash: $block_previous_hash, timestamp: $timestamp})""",
                        block_height=block_height,
                        block_hash=block_hash,
                        block_previous_height=block_previous_height,
                        block_previous_hash=block_previous_hash,
                        timestamp=timestamp,
                    )

                transactions = block["tx"]
                for txs in transactions:
                    tx_id = txs["txid"]
                    fee = Decimal(txs.get("fee", 0))
                    fee_satoshi = int(fee * Decimal("100000000"))
                    session.run(
                        """
                             MATCH (b:Block {height: $block_height})
                             CREATE (t:Transaction {tx_id: $tx_id, block_height: $block_height, fee_satoshi: $fee_satoshi, size: $size, timestamp: $timestamp})
                             CREATE (b)-[:CONTAINS]->(t)
                             """,
                        block_height=block_height,
                        tx_id=tx_id,
                        fee_satoshi=fee_satoshi,
                        size=txs["size"],
                        timestamp=timestamp,
                    )

                    for vin in txs["vin"]:
                        if "coinbase" in vin:
                            session.run(
                                """
                                    MATCH (t:Transaction { tx_id: $tx_id })
                                    CREATE (c:Coinbase { coinbase: $coinbase })
                                    CREATE (c)-[:IN]->(t)
                                    """,
                                tx_id=tx_id,
                                coinbase=vin["coinbase"],
                            )
                        else:
                            prev_tx_id = vin.get("txid")
                            prev_vout = vin.get("vout")
                            if prev_tx_id and prev_vout is not None:
                                # Link vin to its previous tx
                                session.run(
                                    """
                                    MATCH (t:Transaction { tx_id: $tx_id})
                                    CREATE (o:Output {tx_id: $prev_tx_id, vout: $prev_vout })
                                    CREATE (prev:Transaction {tx_id: $prev_tx_id})
                                    CREATE (o)-[:OUT]->(t)
                                    CREATE (o)-[:IN]->(prev)
                                    """,
                                    tx_id=tx_id,
                                    prev_tx_id=prev_tx_id,
                                    prev_vout=prev_vout,
                                )

                    for vout in txs["vout"]:
                        value_satoshi = int(
                            Decimal(vout["value"]) * Decimal("100000000")
                        )
                        n = vout["n"]
                        scriptPubKey = vout["scriptPubKey"]
                        script_type = scriptPubKey.get("type", "unknown")
                        address = scriptPubKey.get("address", None)

                        # Create Vout node and relationship to Transaction
                        session.run(
                            """
                                MATCH (t:Transaction {tx_id: $tx_id})
                                CREATE (o:Output {n: $n, value_satoshi: $value_satoshi, script_type: $script_type})
                                CREATE (t)-[:OUT]->(o)
                                """,
                            tx_id=tx_id,
                            n=n,
                            value_satoshi=value_satoshi,
                            script_type=script_type,
                        )

                        # Create Address nodes and relationships to Vout
                        if address is not None:
                            session.run(
                                """
                                    MATCH (o:Output {n: $n, value_satoshi: $value_satoshi})
                                    CREATE (a:Address {address: $address})
                                    CREATE (o)-[:LOCKED]->(a)
                                    """,
                                n=n,
                                value_satoshi=value_satoshi,
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

    from decimal import Decimal

    def create_graph_from_block(self, block):
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
