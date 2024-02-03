import os
import typing

from neo4j import GraphDatabase


class GraphSearch:
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

    def execute_query(self, network, query):
        # TODO: Implement this
        return []

    def get_block_transaction(self, block_height):
        with self.driver.session() as session:
            data_set = session.run(
                """
                MATCH (t:Transaction { block_height: $block_height })
                RETURN t.block_height AS block_height, COUNT(t) AS transaction_count
                """,
                block_height=block_height
            )
            result = data_set.single()
            return {
                "block_height": result["block_height"],
                "transaction_count": result["transaction_count"]
            }

    def get_run_id(self):
        records, summary, keys = self.driver.execute_query("RETURN 1")
        return summary.metadata.get('run_id', None)

    def get_block_transactions(self, block_heights: typing.List[int]):
        with self.driver.session() as session:
            query = """
                UNWIND $block_heights AS block_height
                MATCH (t:Transaction { block_height: block_height })
                RETURN block_height, COUNT(t) AS transaction_count
            """
            data_set = session.run(query, block_heights=block_heights)

            results = []
            for record in data_set:
                results.append({
                    "block_height": record["block_height"],
                    "transaction_count": record["transaction_count"]
                })

            return results

    def get_block_range(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Transaction)
                RETURN MAX(t.block_height) AS latest_block_height, MIN(t.block_height) AS start_block_height
                """
            )
            single_result = result.single()
            if single_result[0] is None:
                return {
                    'latest_block_height': 0,
                    'start_block_height':0
                }

            return {
                'latest_block_height': single_result[0],
                'start_block_height': single_result[1]
            }

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
