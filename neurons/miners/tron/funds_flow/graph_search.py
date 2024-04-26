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

    def close(self):
        self.driver.close()

    def get_block_transaction(self, block_number):
        with self.driver.session() as session:
            data_set = session.run(
                """
                MATCH (a1:Address)-[s: SENT { block_number: $block_number }]-> (a2: Address)
                RETURN s.block_number AS block_number, COUNT(s) AS transaction_count
                """,
                block_number=block_number
            )
            result = data_set.single()
            return {
                "block_number": result["block_number"],
                "transaction_count": result["transaction_count"]
            }

    def execute_query(self, query):
        with self.driver.session() as session:
            if not is_malicious(query):
                result = session.run(query)
                return result
            else:
                return None

    def get_block_transactions(self, block_number: typing.List[int]):
        with self.driver.session() as session:
            query = """
                UNWIND $block_number AS block_number
                MATCH (a1:Address)-[s: SENT { block_number: block_number }]-> (a2: Address)
                RETURN block_number, COUNT(s) AS transaction_count
            """
            data_set = session.run(query, block_number=block_number)

            results = []
            for record in data_set:
                results.append({
                    "block_number": record["block_number"],
                    "transaction_count": record["transaction_count"]
                })

            return results

    def get_block_range(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a1:Address)-[s: SENT]-> (a2: Address)
                RETURN MAX(s.block_number) AS latest_block_number, MIN(s.block_number) AS start_block_number
                """
            )
            single_result = result.single()
            if single_result[0] is None:
                return {
                    'latest_block_number': 0,
                    'start_block_number':0
                }

            return {
                'latest_block_number': single_result[0],
                'start_block_number': single_result[1]
            }

    def get_latest_block_number(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a1:Address)-[s: SENT]-> (a2: Address)
                RETURN MAX(s.block_number) AS latest_block_number
                """
            )
            single_result = result.single()
            if single_result[0] is None:
                return 0
            return single_result[0]
    
    def solve_challenge(self, checksum):
        with self.driver.session() as session:
            data_set = session.run(
                """
                MATCH (s: Checksum { checksum: $checksum })
                RETURN s.tx_hash
                """,
                checksum=checksum
            )
            single_result = data_set.single()

            if single_result[0] is None:
                return 0
            return single_result[0]

    def get_min_max_block_height(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:SENT)
                RETURN MIN(t.block_number) AS min_block_height, MAX(t.block_number) AS max_block_height
                """
            )
            single_result = result.single()
            if single_result is None:
                return [0, 0]
            return single_result.get('min_block_height'), single_result.get('max_block_height')

    def get_min_max_block_height_cache(self):
        with self.driver.session() as session:
            result_min = session.run(
                """
                MATCH (n:Cache {field: 'min_block_height'})
                RETURN n.value;
                """
            ).single()
            
            result_max = session.run(
                """
                MATCH (n:Cache {field: 'max_block_height'})
                RETURN n.value;
                """
            ).single()
            
            min_block_height = result_min[0] if result_min else 0
            max_block_height = result_max[0] if result_max else 0

            return min_block_height, max_block_height