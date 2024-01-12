import os
from neo4j import GraphDatabase
from decimal import Decimal

from neurons.setup_logger import setup_logger
from neurons.nodes.evm.ethereum.node import EthereumNode
from neurons.miners.ethereum.funds_flow.graph_creator import GraphCreator

logger = setup_logger("EthereumGraphIndexer")

class GraphIndexer:
    def __init__(
        self,
        graph_db_url: str = None,
        graph_db_user: str = None,
        graph_db_password: str = None,
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

    def close(self):
        self.driver.close()

    def get_latest_block_number(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH ()-[r:SENT]->()
                RETURN MAX(r.block_number) AS latest_block_height
                """
            )
            single_result = result.single()
            if single_result[0] is None:
               return 0

            return single_result[0]
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
                "Address-balance": "CREATE INDEX ON :Address(balance);",
                "Address-timestamp": "CREATE INDEX ON :Address(balance);",
                "Address-address": "CREATE INDEX ON :Address(address);",
                "SENT-value": "CREATE INDEX ON :SENT(value)",
                "SENT-symbol": "CREATE INDEX ON :SENT(symbol)",
            }

            for index_name, statement in index_creation_statements.items():
                if index_name not in existing_index_set:
                    try:
                        logger.info(f"Creating index: {index_name}")
                        session.run(statement)
                    except Exception as e:
                        logger.error(f"An exception occurred while creating index {index_name}: {e}")

    def create_graph_focused_on_funds_flow(self, in_memory_graph, batch_size=8):
        block_node = in_memory_graph["block"]
        transactions = block_node.transactions
        with self.driver.session() as session:
            # start memgraph transaction
            transaction = session.begin_transaction()
            
            try:
                for i in range(0, len(transactions), batch_size):
                    batch_transactions = transactions[i : i + batch_size]

                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (from:Address {id: tx.from_address})
                        SET from.timestamp = tx.timestamp,
                            from.balance = tx.from_balance,
                            from.address = tx.from_address
                        MERGE (to:Address {id: tx.to_address})
                        SET to.timestamp = tx.timestamp,
                            to.balance = tx.to_balance,
                            to.address = tx.to_address
                        """,
                        transactions = [
                            {
                                "timestamp": tx.timestamp,
                                "from_address": tx.from_account.address,
                                "from_balance": str(tx.from_account.balance),
                                "to_address": tx.to_account.address,
                                "to_balance": str(tx.to_account.balance),
                            }
                            for tx in batch_transactions
                        ],
                    )
                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (from:Address {id: tx.from_address})
                        MERGE (to:Address {id: tx.to_address})
                        CREATE (from)-[:SENT { tx_hash: tx.tx_hash, block_number:tx.block_number, value: tx.value, fee: tx.fee_wei, timestamp: tx.timestamp, symbol:tx.symbol }]->(to)
                        """,
                        transactions = [
                            {
                                "tx_hash": tx.tx_hash,
                                "block_number": tx.block_number,
                                "value": str(tx.value_wei),
                                "fee_wei": str(tx.gas_amount * tx.gas_price_wei),
                                "timestamp": tx.timestamp,
                                "symbol": tx.symbol
                            }
                            for tx in batch_transactions
                        ]
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
