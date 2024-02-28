import os

from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    graph_indexer = GraphIndexer()
    graph_search = GraphSearch()
    
    print("Creating indexes...")
    
    graph_indexer.create_indexes()
    
    print("Executing cypher query...")
    
    indexed_min_block_height, indexed_max_block_height = graph_search.get_min_max_block_height()
    graph_indexer.set_min_max_block_height_cache(indexed_min_block_height, indexed_max_block_height)

    print(f"Updated min/max cache: ({indexed_min_block_height}, {indexed_max_block_height})")

    graph_search.close()
    graph_indexer.close()