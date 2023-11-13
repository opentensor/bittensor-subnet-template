from neo4j import GraphDatabase

from neurons.miners.configs import GraphDatabaseConfig


class GraphSearch:
    def __init__(self, config: GraphDatabaseConfig):
        self.driver = GraphDatabase.driver(
            config.graph_db_url,
            auth=(config.graph_db_user, config.graph_db_password),
        )

    def execute_query(self, network, asset, query):
        # filterout dangerous keywords: delete, create, merge  etc...
        return []

    def get_random_block_transaction(self):
        with self.neo4j_handler.driver.session() as session:
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
                "block_height": data_set.single()["block_height"],
                "total_value_satoshi": data_set.single()["total_value_satoshi"],
                "transaction_count": data_set.single()["transaction_count"],
            }
