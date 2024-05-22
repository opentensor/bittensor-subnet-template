import os

from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    graph_indexer = GraphIndexer()
    
    print("Executing cypher query...")
    indexed_block_height_ranges = graph_indexer.find_indexed_cache_height_ranges()
    print(f"Found indexed block height ranges: {indexed_block_height_ranges}")
