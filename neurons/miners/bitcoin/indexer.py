import time
from neurons.miners.bitcoin.bitcoin_node import BitcoinNode
from neurons.miners.bitcoin.configs import IndexerConfig
from neurons.miners.bitcoin.graph_indexer import GraphIndexer


def index_blocks(_bitcoin_node, _graph_indexer):
    while True:
        start_height = _graph_indexer.get_latest_block_number() + 1
        current_block_height = _bitcoin_node.get_current_block_height()

        if start_height > current_block_height:
            print(f"Waiting for new blocks. Current height is {current_block_height}.")
            time.sleep(60)  # Wait for a minute before checking for new blocks
            continue

        for block_height in range(start_height, current_block_height + 1):
            print(f"Indexing block {block_height}")
            transactions = _bitcoin_node.get_transactions_from_block_height(
                block_height
            )
            _graph_indexer.create_transaction_graph([(block_height, transactions)])


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    indexer_config = IndexerConfig()
    bitcoin_node = BitcoinNode(config=indexer_config.node_config)
    graph_indexer = GraphIndexer(config=indexer_config.graph_config)

    print("Starting indexer")
    print(f"Current config: {indexer_config}")
    print(f"Current block height: {bitcoin_node.get_current_block_height()}")
    print(f"Latest block height: {graph_indexer.get_latest_block_number()}")

    try:
        index_blocks(bitcoin_node, graph_indexer)
    finally:
        graph_indexer.close()

    print("Indexer stopped")

# TODO
"""
- wait for blockchain sync
- run this scrip and check if it works fine
- add parametrization
- add manual in readme
- add dockerfile running indexer.py in apline linux as continous service

- later: setup docker repository on github
- setup gitchub build and publishing to dockerhub from master branch and versioning

- add support for litecoin
- do refactoring, probably single miner will be needed,as it will be only serving requests to neo4j

"""
