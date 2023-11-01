from neo4j import GraphDatabase


class GraphSearch:
    def __init__(self, neo4j_handler):
        self.neo4j_handler = neo4j_handler

    def get_top_addresses_by_amount(self, limit=100):
        top_addresses_query = """
        MATCH (a:Address)-[:TO_ADDRESS]-(v:Vout)
        RETURN a.address AS address, SUM(v.value) AS total_amount
        ORDER BY total_amount DESC
        LIMIT $limit
        """
        with self.neo4j_handler.driver.session() as session:
            result = session.run(top_addresses_query, limit=limit)
            return [
                {"address": record["address"], "total_amount": record["total_amount"]}
                for record in result
            ]


# Example usage
"""
neo4j_handler = Neo4jHandler(uri="bolt://localhost:7687", user="neo4j", password="password")
bitcoin_graph_search = BitcoinGraphSearch(neo4j_handler)

# Get the top 100 addresses by total amount
top_addresses = bitcoin_graph_search.get_top_addresses_by_amount()
for address in top_addresses:
    print(address)

# Don't forget to close the Neo4j driver connection
neo4j_handler.close()
"""
