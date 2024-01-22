import os
from neurons.setup_logger import setup_logger
from neo4j import GraphDatabase


logger = setup_logger("GraphIndexer")


class GraphIndexer:
    def __init__(
        self,
        url: str = None,
        user: str = None,
        password: str = None,
    ):
        self.driver = GraphDatabase.driver(
            url,
            auth=(user, password),
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
                        logger.error(f"An exception occurred while creating index {index_name}: {e}")

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

                transaction.commit()
                return True

            except Exception as e:
                transaction.rollback()
                logger.error(f"An exception occurred: {e}")
                return False

            finally:
                if transaction.closed() is False:
                    transaction.close()
