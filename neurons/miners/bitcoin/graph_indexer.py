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
            result = session.run("MATCH (b:Block) RETURN MAX(b.number) AS latest_block")
            single_result = result.single()
            if single_result[0] is None:
                return 0
            return single_result[0]

    from decimal import Decimal, getcontext

    # Set the precision high enough to handle satoshis for Bitcoin transactions
    getcontext().prec = 28

    from neo4j import Transaction

    def create_transaction_graph(self, transactions):
        # Cypher query to create a Block and Transaction nodes, and the CONTAINS relationship
        create_block_tx_query = """
        UNWIND $data as row
        MERGE (b:Block {number: row.block_height})
        WITH b, row
        UNWIND row.txs as tx
        MERGE (t:Transaction {id: tx.txid, type: tx.type})
        MERGE (b)-[:CONTAINS]->(t)
        RETURN count(t) as transactionsCreated
        """

        # Cypher query to create Coinbase, Vin, Vout, and Address nodes and their relationships
        create_vin_vout_address_query = """
        UNWIND $data as row
        MATCH (t:Transaction {id: row.txid})
        WITH t, row
        WHERE row.vin IS NOT NULL AND row.vout IS NOT NULL
        FOREACH (input IN row.vin | 
            MERGE (v:Vin {txid: input.prev_txid, vout: input.prev_vout})
            MERGE (prev:Transaction {id: input.prev_txid})
            MERGE (v)-[:VIN_OF]->(t)
            MERGE (v)-[:VOUT_REF]->(prev)
        )
        FOREACH (output IN row.vout | 
            MERGE (v:Vout {n: output.n, value: output.value_satoshi, script_type: output.script_type})
            MERGE (t)-[:VOUT]->(v)
            FOREACH (address IN output.addresses |
                MERGE (a:Address {address: address})
                MERGE (v)-[:TO_ADDRESS]->(a)
            )
        )
        RETURN count(t) as transactionsProcessed
        """

        # Convert transactions to a format suitable for parameterized queries with batching
        block_tx_data = []
        vin_vout_address_data = []

        for block_height, txs in transactions:
            block_tx_row = {"block_height": block_height, "txs": []}
            for tx in txs:
                txid = tx["txid"]
                tx_type = tx.get(
                    "type", "unknown"
                )  # Add a default type if not specified
                tx_data = {"txid": txid, "type": tx_type}
                block_tx_row["txs"].append(tx_data)

                vin_data = []
                vout_data = []

                # Handle inputs (vins)
                for vin in tx.get("vin", []):
                    if "coinbase" in vin:
                        # Handle coinbase transactions differently
                        vin_data.append({"coinbase": vin["coinbase"]})
                    else:
                        prev_txid = vin.get("txid")
                        prev_vout = vin.get("vout")
                        if prev_txid and prev_vout is not None:
                            vin_data.append(
                                {"prev_txid": prev_txid, "prev_vout": prev_vout}
                            )

                # Handle outputs (vouts)
                for vout in tx.get("vout", []):
                    value_satoshi = int(Decimal(vout["value"]) * Decimal("100000000"))
                    n = vout["n"]
                    script_type = vout["scriptPubKey"].get("type", "unknown")
                    addresses = vout["scriptPubKey"].get("addresses", [])
                    vout_data.append(
                        {
                            "n": n,
                            "value_satoshi": value_satoshi,
                            "script_type": script_type,
                            "addresses": addresses,
                        }
                    )

                vin_vout_address_data.append(
                    {"txid": txid, "vin": vin_data, "vout": vout_data}
                )

            block_tx_data.append(block_tx_row)

        # Use the driver's session to execute the batched operations
        with self.driver.session() as session:
            # Execute batch creation of Block and Transaction nodes
            session.run(create_block_tx_query, data=block_tx_data)

            # Execute batch creation of Coinbase, Vin, Vout, and Address nodes and relationships
            session.run(create_vin_vout_address_query, data=vin_vout_address_data)

    def create_transaction_graph2(self, transactions):
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
