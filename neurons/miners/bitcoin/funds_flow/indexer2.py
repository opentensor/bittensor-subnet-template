import os
import time
import signal
from neurons.setup_logger import setup_logger
from neurons.nodes.factory import NodeFactory
from neurons.miners.bitcoin.funds_flow.graph_creator import GraphCreator
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch

from insights.protocol import NETWORK_BITCOIN

from sqlalchemy import create_engine, types


# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("Indexer")

def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True

def index_block(_bitcoin_node, _graph_creator, _graph_indexer, _graph_search, block_height):
    block = _bitcoin_node.get_block_by_height(block_height)
    num_transactions = len(block["tx"])
    start_time = time.time()
    in_memory_graph = _graph_creator.create_in_memory_graph_from_block(block)
    success = _graph_indexer.create_graph_focused_on_money_flow(in_memory_graph, _bitcoin_node)
    end_time = time.time()
    time_taken = end_time - start_time
    formatted_num_transactions = "{:>4}".format(num_transactions)
    formatted_time_taken = "{:6.2f}".format(time_taken)
    formatted_tps = "{:8.2f}".format(
        num_transactions / time_taken if time_taken > 0 else float("inf")
    )

    if time_taken > 0:
        logger.info(
            "Block {:>6}: Processed {} transactions in {} seconds {} TPS".format(
                block_height,
                formatted_num_transactions,
                formatted_time_taken,
                formatted_tps,
            )
        )
    else:
        logger.info(
            "Block {:>6}: Processed {} transactions in 0.00 seconds (  Inf TPS).".format(
                block_height, formatted_num_transactions
            )
        )
        
    min_block_height_cache, max_block_height_cache = _graph_search.get_min_max_block_height_cache()
    if min_block_height_cache is None:
        min_block_height_cache = block_height
    if max_block_height_cache is None:
        max_block_height_cache = block_height
        
    _graph_indexer.set_min_max_block_height_cache(min(min_block_height_cache, block_height), max(max_block_height_cache, block_height))

    return success


def move_forward(_bitcoin_node, _graph_creator, _graph_indexer, _graph_search, start_height: int):
    global shutdown_flag

    skip_blocks = 6
    block_height = start_height
    
    while not shutdown_flag:
        current_block_height = _bitcoin_node.get_current_block_height() - skip_blocks
        if block_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)
            continue
        
        if _graph_indexer.check_if_block_is_indexed(block_height):
            logger.info(f"Skipping block #{block_height}. Already indexed.")
            block_height += 1
            continue
        
        success = index_block(_bitcoin_node, _graph_creator, _graph_indexer, _graph_search, block_height)
        
        if success:
            block_height += 1
        else:
            logger.error(f"Failed to index block {block_height}.")
            time.sleep(30)

# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    bitcoin_node = NodeFactory.create_node(NETWORK_BITCOIN)
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()
    graph_search = GraphSearch()
