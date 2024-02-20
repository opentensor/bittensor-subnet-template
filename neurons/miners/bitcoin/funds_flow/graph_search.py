import os
import typing
from neo4j import GraphDatabase

from neurons.utils import is_malicious


class GraphSearch:
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

    def execute_query(self, query):
        with self.driver.session() as session:
            if not is_malicious(query):
                result = session.run(query)
                return result
            else:
                return None


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

    def solve_challenge(self, in_total_amount: int, out_total_amount: int, tx_id_last_4_chars: str) -> str:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Transaction {out_total_amount: $out_total_amount})
                WHERE t.in_total_amount = $in_total_amount AND t.tx_id ENDS WITH $tx_id_last_4_chars
                RETURN t.tx_id;
                """,
                in_total_amount=in_total_amount,
                out_total_amount=out_total_amount,
                tx_id_last_4_chars=tx_id_last_4_chars
            )
            single_result = result.single()
            if single_result is None or single_result[0] is None:
                return None
            return single_result[0]