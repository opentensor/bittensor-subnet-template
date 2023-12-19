import os

from bitcoinrpc.authproxy import AuthServiceProxy

from neurons.setup_logger import setup_logger
from neo4j import GraphDatabase


logger = setup_logger("GraphIndexer")


class GraphIndexer:
    def __init__(
        self,
        graph_db_url: str = None,
        graph_db_user: str = None,
        graph_db_password: str = None,
        rpc: AuthServiceProxy = None,
    ):
        if graph_db_url is None:
            self.graph_db_url = (
                os.environ.get("GRAPH_DB_URL") or "bolt://localhost:7687"
            )
        else:
            self.graph_db_url = graph_db_url

        if graph_db_user is None:
            self.graph_db_user = os.environ.get("GRAPH_DB_USER") or ""
        else:
            self.graph_db_user = graph_db_user

        if graph_db_password is None:
            self.graph_db_password = os.environ.get("GRAPH_DB_PASSWORD") or ""
        else:
            self.graph_db_password = graph_db_password

        self.driver = GraphDatabase.driver(
            self.graph_db_url,
            auth=(self.graph_db_user, self.graph_db_password),
        )

        self.bitcoin_rpc = rpc

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

    from decimal import getcontext

    # Set the precision high enough to handle satoshis for Bitcoin transactions
    getcontext().prec = 28

    def create_indexes(self):
        with self.driver.session() as session:
            # Fetch existing indexes
            existing_indexes = session.run("SHOW INDEX INFO")
            existing_index_set = set()
            for record in existing_indexes:
                label = record["label"]
                property = record["property"]
                index_name = f"{label}-{property}"
                if index_name:
                    existing_index_set.add(index_name)

            index_creation_statements = {
                "Transaction-tx_id": "CREATE INDEX ON :Transaction(tx_id);",
                "Transaction-block_height": "CREATE INDEX ON :Transaction(block_height);",
                "Address-address": "CREATE INDEX ON :Address(address);",
                "SENT-value_satoshi": "CREATE INDEX ON :SENT(value_satoshi)",
            }

            for index_name, statement in index_creation_statements.items():
                if index_name not in existing_index_set:
                    try:
                        logger.info(f"Creating index: {index_name}")
                        session.run(statement)
                    except Exception as e:
                        print(
                            f"An exception occurred while creating index {index_name}: {e}"
                        )

    def fetch_block_data(self, block_height):
        """
        Fetches block data using Bitcoin RPC AuthServiceProxy.

        :param block_height: The height of the block to fetch.
        :return: The block data.
        """

        # Ensure AuthServiceProxy object is available
        if not hasattr(self, "bitcoin_rpc") or self.bitcoin_rpc is None:
            raise Exception("Bitcoin RPC AuthServiceProxy is not configured")

        try:
            # Fetch block hash for the given height
            block_hash = self.bitcoin_rpc.getblockhash(block_height)

            # Fetch block data using the block hash
            block_data = self.bitcoin_rpc.getblock(
                block_hash, 2
            )  # 2 for verbose mode (transaction details)
            return block_data

        except Exception as e:
            logger.error(f"Error fetching block data: {e}")
            return None

    def store_block_data(self, block_data):
        with self.driver.session() as session:
            try:
                block_node = session.run(
                    "CREATE (b:Block {number: $number, hash: $hash}) RETURN b",
                    number=block_data["height"],
                    hash=block_data["hash"],
                )
                for tx in block_data["tx"]:
                    tx_node = session.run(
                        "CREATE (t:Transaction {hash: $hash}) RETURN t",
                        hash=tx["hash"],
                    )
                    session.run(
                        "MATCH (b:Block), (t:Transaction) WHERE b.hash = $block_hash AND t.hash = $tx_hash CREATE (b)-[:CONTAINS]->(t)",
                        block_hash=block_data["hash"],
                        tx_hash=tx["hash"],
                    )
            except Exception as e:
                logger.error(f"Error storing block data: {e}")

    def reverse_index_blocks(self, start_block):
        current_block = start_block
        while current_block >= 0:
            block_data = self.fetch_block_data(current_block)
            if block_data:
                self.store_block_data(block_data)
            else:
                logger.error(f"Failed to fetch data for block {current_block}")

            current_block -= 1  # Move to the previous block

    def create_graph_focused_on_money_flow(self, in_memory_graph, batch_size=8):
        block_node = in_memory_graph["block"]
        transactions = block_node.transactions

        with self.driver.session() as session:
            # Start a transaction
            transaction = session.begin_transaction()

            try:
                for i in range(0, len(transactions), batch_size):
                    batch_transactions = transactions[i : i + batch_size]

                    # Process transactions in the current batch
                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (t:Transaction {tx_id: tx.tx_id})
                        ON CREATE SET t.timestamp = tx.timestamp,
                                      t.block_height = tx.block_height,
                                      t.is_coinbase = tx.is_coinbase
                        """,
                        transactions=[
                            {
                                "tx_id": tx.tx_id,
                                "timestamp": tx.timestamp,
                                "block_height": tx.block_height,
                                "is_coinbase": tx.is_coinbase,
                            }
                            for tx in batch_transactions
                        ],
                    )

                    # Process all vouts for transactions in the current batch
                    batch_vouts = []
                    for tx in batch_transactions:
                        for index, vout in enumerate(tx.vouts):
                            batch_vouts.append(
                                {
                                    "tx_id": tx.tx_id,
                                    "address": vout.address,
                                    "value_satoshi": vout.value_satoshi,
                                    "is_coinbase": tx.is_coinbase
                                    and index
                                    == 0,  # True only for the first vout of a coinbase transaction
                                }
                            )

                    transaction.run(
                        """
                        UNWIND $vouts AS vout
                        MERGE (a:Address {address: vout.address})
                        MERGE (t:Transaction {tx_id: vout.tx_id})
                        CREATE (t)-[:SENT { value_satoshi: vout.value_satoshi, is_coinbase: vout.is_coinbase }]->(a)
                        """,
                        vouts=batch_vouts,
                    )

                # Commit the transaction
                transaction.commit()
                return True

            except Exception as e:
                # Roll back the transaction in case of an error
                transaction.rollback()
                print(f"An exception occurred: {e}")
                return False

            finally:
                # Close the transaction
                if transaction.closed() is False:
                    transaction.close()
