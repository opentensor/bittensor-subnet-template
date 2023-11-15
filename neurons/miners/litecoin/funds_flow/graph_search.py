import os
from neo4j import GraphDatabase


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

    def execute_query(self, network, query):
        # filterout dangerous keywords: delete, create, merge  etc...
        return []

    def verify_random_block_transaction(self):
        with self.driver.session() as session:
            data_set = session.run(
                """
                MATCH (t:Transaction)
                WITH COLLECT(DISTINCT t.block_height) AS blockHeights
                WITH blockHeights, blockHeights[TOINTEGER(RAND() * SIZE(blockHeights))] AS randomBlockHeight
                WITH [randomBlockHeight] AS randomBlockHeightList
                UNWIND randomBlockHeightList AS rbh
                MATCH (t:Transaction { block_height: rbh })-[r:SENT]->(a:Address)
                RETURN SUM(r.value_satoshi) AS total_value_satoshi, COUNT(t) AS transaction_count
                """
            )
            return {
                "total_value_satoshi": data_set.single()["total_value_satoshi"],
                "transaction_count": data_set.single()["transaction_count"],
            }
