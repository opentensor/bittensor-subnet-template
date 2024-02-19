import os

from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    graph_db_url = (
        os.environ.get("GRAPH_DB_URL") or "bolt://localhost:7687"
    )
    graph_db_user = os.environ.get("GRAPH_DB_USER") or ""
    graph_db_password = os.environ.get("GRAPH_DB_PASSWORD") or ""
    
    graph_search = GraphSearch(
        graph_db_url=os.environ.get('GRAPH_DB_URL'),
        graph_db_user=os.environ.get('GRAPH_DB_USER'),
        graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
    )
    
    print("Executing cypher query...")
    indexed_block_height_ranges = graph_search.find_indexed_block_height_ranges()
    print(f"Found indexed block height ranges: {indexed_block_height_ranges}")
