import os
from neurons.setup_logger import setup_logger
from neo4j import GraphDatabase

logger = setup_logger("ReverseGraphIndexer")


class ReverseGraphIndexer:
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
            auth=(graph_db_user, self.graph_db_password),
        )

    def close(self):
        self.driver.close()

    def get_first_indexed_block(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Transaction)
                RETURN MIN(t.block_height) AS latest_block_height
                """
            )
            single_result = result.single()
            if single_result is None:
                return 0

            return single_result[0]

    from decimal import getcontext

    # satoshi precision

    getcontext().prec = 28
