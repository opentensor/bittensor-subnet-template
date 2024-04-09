import os
from neurons.setup_logger import setup_logger
from sqlalchemy import create_engine, types

logger = setup_logger("BalanceIndexer")


class BalanceIndexer:
    def __init__(
        self,
        postgres_host,
        postgres_port,
        postgres_db,
        postgres_user,
        postgres_password,
    ):
        if postgres_host is None:
            self.postgres_host = (
                os.environ.get("POSTGRES_HOST") or '127.0.0.1'
            )
        else:
            self.postgres_host = postgres_host

        if postgres_port is None:
            self.postgres_port = os.environ.get("POSTGRES_PORT") or 5432
        else:
            self.postgres_port = postgres_port

        if postgres_db is None:
            self.postgres_db = os.environ.get("POSTGRES_DB") or 'bitcoin'
        else:
            self.postgres_db = postgres_db
            
        if postgres_user is None:
            self.postgres_user = os.environ.get("POSTGRES_USER") or ''
        else:
            self.postgres_user = postgres_user
            
        if postgres_password is None:
            self.postgres_password = os.environ.get("POSTGRES_PASSWORD") or ''
        else:
            self.postgres_password = postgres_password

        self.engine = create_engine(f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}')

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
        
    def check_if_block_is_indexed(self, block_height: int) -> bool:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t: Transaction{block_height: $block_height})
                RETURN t
                LIMIT 1;
                """,
                block_height=block_height
            )
            single_result = result.single()
            return single_result is not None


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
                index_name = f"{label}-{property}" if property else label
                if index_name:
                    existing_index_set.add(index_name)

            index_creation_statements = {
                "Cache": "CREATE INDEX ON :Cache;",
                "Transaction": "CREATE INDEX ON :Transaction;",
                "Transaction-tx_id": "CREATE INDEX ON :Transaction(tx_id);",
                "Transaction-block_height": "CREATE INDEX ON :Transaction(block_height);",
                "Transaction-out_total_amount": "CREATE INDEX ON :Transaction(out_total_amount)",
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

    def create_graph_focused_on_money_flow(self, in_memory_graph, _bitcoin_node, batch_size=8):
        block_node = in_memory_graph["block"]
        transactions = block_node.transactions

        with self.driver.session() as session:
            # Start a transaction
            transaction = session.begin_transaction()

            try:
                for i in range(0, len(transactions), batch_size):
                    batch_transactions = transactions[i : i + batch_size]

                    # Process all transactions, inputs, and outputs in the current batch
                    batch_txns = []
                    batch_inputs = []
                    batch_outputs = []
                    for tx in batch_transactions:
                        in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = _bitcoin_node.process_in_memory_txn_for_indexing(tx)
                        
                        inputs = [{"address": address, "amount": in_amount_by_address[address], "tx_id": tx.tx_id } for address in input_addresses]
                        outputs = [{"address": address, "amount": out_amount_by_address[address], "tx_id": tx.tx_id } for address in output_addresses]

                        batch_txns.append({
                            "tx_id": tx.tx_id,
                            "in_total_amount": in_total_amount,
                            "out_total_amount": out_total_amount,
                            "timestamp": tx.timestamp,
                            "block_height": tx.block_height,
                            "is_coinbase": tx.is_coinbase,
                        })
                        batch_inputs += inputs
                        batch_outputs += outputs

                    transaction.run(
                        """
                        UNWIND $transactions AS tx
                        MERGE (t:Transaction {tx_id: tx.tx_id})
                        ON CREATE SET t.timestamp = tx.timestamp,
                                    t.in_total_amount = tx.in_total_amount,
                                    t.out_total_amount = tx.out_total_amount,
                                    t.timestamp = tx.timestamp,
                                    t.block_height = tx.block_height,
                                    t.is_coinbase = tx.is_coinbase
                        """,
                        transactions=batch_txns,
                    )
                    
                    transaction.run(
                        """
                        UNWIND $inputs AS input
                        MERGE (a:Address {address: input.address})
                        MERGE (t:Transaction {tx_id: input.tx_id})
                        CREATE (a)-[:SENT { value_satoshi: input.amount }]->(t)
                        """,
                        inputs=batch_inputs
                    )
                    
                    transaction.run(
                        """
                        UNWIND $outputs AS output
                        MERGE (a:Address {address: output.address})
                        MERGE (t:Transaction {tx_id: output.tx_id})
                        CREATE (t)-[:SENT { value_satoshi: output.amount }]->(a)
                        """,
                        outputs=batch_outputs
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
