import os
from neo4j import GraphDatabase
from decimal import Decimal

from neurons.setup_logger import setup_logger

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
    
    def set_min_max_block_height_cache(self, min_block_height, max_block_height):
        with self.driver.session() as session:
            # update min block height
            session.run(
                """
                MERGE (n:Cache {field: 'min_block_height'})
                SET n.value = $min_block_height
                RETURN n
                """,
                {"min_block_height": min_block_height}
            )

            # update max block height
            session.run(
                """
                MERGE (n:Cache {field: 'max_block_height'})
                SET n.value = $max_block_height
                RETURN n
                """,
                {"max_block_height": max_block_height}
            )

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
                "Cache-field": "CREATE INDEX ON :Cache(field);",
                "Cache-value": "CREATE INDEX ON :Cache(value);",
                "Checksum-checksum": "CREATE INDEX ON :Checksum(checksum);",
                "Checksum-tx_hash": "CREATE INDEX ON :Checksum(tx_hash);",
                "Address-balance": "CREATE INDEX ON :Address(balance);",
                "Address-timestamp": "CREATE INDEX ON :Address(timestamp);",
                "Address-address": "CREATE INDEX ON :Address(address);",
                "SENT-value": "CREATE INDEX ON :SENT(value)",
                "SENT-block_number": "CREATE INDEX ON :SENT(block_number)",
                "SENT-symbol": "CREATE INDEX ON :SENT(symbol)",
                "SENT-tx_hash": "CREATE INDEX ON :SENT(tx_hash)",
                "SENT-checksum": "CREATE INDEX ON :SENT(checksum)",
            }

            for index_name, statement in index_creation_statements.items():
                if index_name not in existing_index_set:
                    try:
                        logger.info(f"Creating index", index_name = index_name)
                        session.run(statement)
                    except Exception as e:
                        logger.error(f"An exception occurred while creating index", index_name = index_name, error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})

    def create_graph_focused_on_funds_flow(self, transactions, batch_size=8):
        # transactions = in_memory_graph["block"].transactions
        with self.driver.session() as session:
            # start memgraph transaction
            transaction = session.begin_transaction()
            try:
                for i in range(0, len(transactions), batch_size):
                    batch_transactions = transactions[i : i + batch_size]

                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (from:Address {address: tx.from_address})
                        ON CREATE SET from.timestamp = tx.from_timestamp,
                            from.balance = tx.from_balance
                        ON MATCH SET from.balance = CASE
                            WHEN from.timestamp < tx.from_timestamp
                            THEN tx.from_balance ELSE from.balance END,
                            from.timestamp = CASE WHEN from.timestamp < tx.from_timestamp THEN tx.from_timestamp ELSE from.timestamp END
                        MERGE (to:Address {address: tx.to_address})
                        ON CREATE SET to.timestamp = tx.to_timestamp,
                            to.balance = tx.to_balance
                        ON MATCH SET to.balance = CASE
                            WHEN to.timestamp < tx.to_timestamp
                            THEN tx.to_balance ELSE to.balance END,
                            to.timestamp = CASE WHEN to.timestamp < tx.to_timestamp THEN tx.to_timestamp ELSE to.timestamp END
                        MERGE (s:Checksum {checksum: tx.checksum})
                        ON CREATE SET s.checksum = tx.checksum,
                            s.tx_hash = tx.tx_hash
                        """,
                        transactions = [
                            {
                                "from_timestamp": tx.from_address.timestamp,
                                "to_timestamp": tx.to_address.timestamp,
                                "from_address": tx.from_address.address,
                                "from_balance": tx.from_address.balance,
                                "to_address": tx.to_address.address,
                                "to_balance": tx.to_address.balance,
                                "checksum": tx.checksum,
                                "tx_hash": tx.tx_hash,
                            }
                            for tx in batch_transactions
                        ],
                    )

                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (from:Address {address: tx.from_address})
                        MERGE (to:Address {address: tx.to_address})
                        CREATE (from)-[:SENT { tx_hash: tx.tx_hash, block_number:tx.block_number, value: tx.value, fee: tx.fee_wei, timestamp: tx.timestamp, symbol:tx.symbol, from: tx.from_address, to: tx.to_address, checksum:tx.checksum }]->(to)
                        """,
                        transactions = [
                            {
                                "tx_hash": tx.tx_hash,
                                "block_number": tx.block_number,
                                "value": tx.value_wei,
                                "fee_wei": tx.gas_used,
                                "timestamp": tx.timestamp,
                                "symbol": tx.symbol,
                                "from_address": tx.from_address.address,
                                "to_address": tx.to_address.address,
                                "checksum": tx.checksum,
                            }
                            for tx in batch_transactions
                        ]
                    )

                transaction.commit()
                return True

            except Exception as e:
                transaction.rollback()
                logger.error(f"An exception occurred", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})
                return False

            finally:
                if transaction.closed() is False:
                    transaction.close()
