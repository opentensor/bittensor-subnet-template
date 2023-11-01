from neo4j import GraphDatabase

from neurons.miners.bitcoin.configs import GraphIndexerConfig


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

    def create_transaction_graph(self, transactions):
        with self.driver.session() as session:
            for block_height, txs in transactions:
                for tx in txs:
                    txid = tx["txid"]
                    # Create a block node
                    session.run(
                        "MERGE (b:Block {number: $block_height})",
                        block_height=block_height,
                    )
                    # Create a transaction node and link it to the block
                    session.run(
                        """
                                MATCH (b:Block {number: $block_height})
                                MERGE (t:Transaction {id: $txid})
                                MERGE (b)-[:CONTAINS]->(t)
                                """,
                        block_height=block_height,
                        txid=txid,
                    )
                    # Create nodes for vins, vouts, and addresses
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
                            # Link vin to its previous tx
                            session.run(
                                """
                                        MATCH (t:Transaction {id: $txid})
                                        MERGE (v:Vin {txid: $vin_txid, vout: $vout})
                                        MERGE (prev:Transaction {id: $vin_txid})
                                        MERGE (v)-[:VIN_OF]->(t)
                                        MERGE (v)-[:VOUT_REF]->(prev)
                                        """,
                                txid=txid,
                                vin_txid=vin["txid"],
                                vout=vin["vout"],
                            )
                    for vout in tx.get("vout", []):
                        scriptPubKey = vout["scriptPubKey"]
                        addresses = scriptPubKey.get("addresses", [])
                        for address in addresses:
                            session.run(
                                """
                                        MATCH (t:Transaction {id: $txid})
                                        MERGE (a:Address {address: $address})
                                        MERGE (v:Vout {value: $value})
                                        MERGE (t)-[:VOUT]->(v)
                                        MERGE (v)-[:TO_ADDRESS]->(a)
                                        """,
                                txid=txid,
                                address=address,
                                value=vout["value"],
                            )


# Example usage
"""
bitcoin_config = BitcoinNodeConfig()
bitcoin_query = BitcoinQuery(config=bitcoin_config)
neo4j_handler = Neo4jHandler(
    uri="bolt://localhost:7687", user="neo4j", password="password"
)

# Get transactions from a specific block range
transactions = bitcoin_query.get_transactions_from_block_range(
    600000, 600010, bitcoin_config.rpc_url
)
# Store them in the Neo4j graph database
neo4j_handler.create_transaction_graph(transactions)

# Don't forget to close the Neo4j driver connection
neo4j_handler.close()
"""
