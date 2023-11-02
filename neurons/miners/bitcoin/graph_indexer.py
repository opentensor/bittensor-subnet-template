from neo4j import GraphDatabase
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
            result = session.run("MATCH (b:Block) RETURN MAX(b.number) AS latest_block")
            single_result = result.single()
            if single_result[0] is None:
                return 0
            return single_result[0]

    from decimal import Decimal, getcontext

    # Set the precision high enough to handle satoshis for Bitcoin transactions
    getcontext().prec = 28

    def create_transaction_graph(self, transactions):
        with self.driver.session() as session:
            for block_height, txs in transactions:
                for tx in txs:
                    txid = tx["txid"]
                    tx_type = tx.get(
                        "type", "unknown"
                    )  # Add a default type if not specified

                    # Create a block node
                    session.run(
                        "MERGE (b:Block {number: $block_height})",
                        block_height=block_height,
                    )
                    # Create a transaction node with type and link it to the block
                    session.run(
                        """
                        MATCH (b:Block {number: $block_height})
                        MERGE (t:Transaction {id: $txid, type: $tx_type})
                        MERGE (b)-[:CONTAINS]->(t)
                        """,
                        block_height=block_height,
                        txid=txid,
                        tx_type=tx_type,
                    )
                    # Handle inputs (vins)
                    for vin in tx.get("vin", []):
                        if "coinbase" in vin:
                            # Handle coinbase transactions differently
                            session.run(
                                """
                                MATCH (t:Transaction {id: $txid})
                                MERGE (c:Coinbase {id: $coinbase})
                                MERGE (t)-[:COINBASE_INPUT]->(c)
                                """,
                                txid=txid,
                                coinbase=vin["coinbase"],
                            )
                        else:
                            prev_txid = vin.get("txid")
                            prev_vout = vin.get("vout")
                            if prev_txid and prev_vout is not None:
                                # Link vin to its previous tx
                                session.run(
                                    """
                                    MATCH (t:Transaction {id: $txid})
                                    MERGE (v:Vin {txid: $prev_txid, vout: $prev_vout})
                                    MERGE (prev:Transaction {id: $prev_txid})
                                    MERGE (v)-[:VIN_OF]->(t)
                                    MERGE (v)-[:VOUT_REF]->(prev)
                                    """,
                                    txid=txid,
                                    prev_txid=prev_txid,
                                    prev_vout=prev_vout,
                                )

                    # Handle outputs (vouts)
                    for vout in tx.get("vout", []):
                        # Convert value from BTC to satoshi
                        value_satoshi = int(
                            Decimal(vout["value"]) * Decimal("100000000")
                        )  # Use strings to avoid float

                        n = vout["n"]  # The index of the output in the transaction
                        scriptPubKey = vout["scriptPubKey"]
                        script_type = scriptPubKey.get(
                            "type", "unknown"
                        )  # Add a default script type if not specified
                        addresses = scriptPubKey.get("addresses", [])

                        # Create Vout node and relationship to Transaction
                        session.run(
                            """
                            MATCH (t:Transaction {id: $txid})
                            MERGE (v:Vout {n: $n, value: $value_satoshi, script_type: $script_type})
                            MERGE (t)-[:VOUT]->(v)
                            """,
                            txid=txid,
                            n=n,
                            value_satoshi=value_satoshi,
                            script_type=script_type,
                        )

                        # Create Address nodes and relationships to Vout
                        for address in addresses:
                            session.run(
                                """
                                MATCH (v:Vout {n: $n, value: $value_satoshi})
                                MERGE (a:Address {address: $address})
                                MERGE (v)-[:TO_ADDRESS]->(a)
                                """,
                                n=n,
                                value_satoshi=value_satoshi,
                                address=address,
                            )
