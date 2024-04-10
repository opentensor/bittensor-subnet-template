import os
import signal
import time
from neurons.setup_logger import setup_logger
from neurons.nodes.factory import NodeFactory
from neurons.nodes.bitcoin.node_utils import parse_block_data
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch

from insights.protocol import NETWORK_BITCOIN

# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("Indexer")


def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True


def index_block(_bitcoin_node, _graph_indexer, _graph_search, block_height):
    block = _bitcoin_node.get_block_by_height(block_height)
    num_transactions = len(block["tx"])
    start_time = time.time()
    block_data = parse_block_data(block)
    success = _graph_indexer.create_graph_focused_on_money_flow(block_data, _bitcoin_node)
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


def iterate_range(_bitcoin_node, _graph_indexer, _graph_search, start_height: int, end_height: int, in_reverse_order: bool = False):
    if in_reverse_order and start_height < end_height:
        logger.error("start_height must equal or greater than end_height in reverse indexer")
        return False
    if not in_reverse_order and start_height > end_height:
        logger.error("start_height must equal or less than end_height in reverse indexer")
        return False
    
    global shutdown_flag
    
    block_height = start_height
    step = -1 if in_reverse_order else +1
    
    while (block_height - end_height) * step <= 0 and not shutdown_flag:
        if _graph_indexer.check_if_block_is_indexed(block_height):
            logger.info(f"Skipping block #{block_height}. Already indexed.")
            block_height += step
            continue
        
        success = index_block(_bitcoin_node, _graph_indexer, _graph_search, block_height)
        
        if success:
            block_height += step
        else:
            logger.error(f"Failed to index block {block_height}.")
            time.sleep(30)
            
    return True


def move_forward(_bitcoin_node, _graph_indexer, _graph_search, start_height: int):
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
        
        success = index_block(_bitcoin_node, _graph_indexer, _graph_search, block_height)
        
        if success:
            block_height += 1
        else:
            logger.error(f"Failed to index block {block_height}.")
            time.sleep(30)
            
            
def do_smart_indexing(_bitcoin_node, _graph_indexer, _graph_search, start_height: int):
    global shutdown_flag

    skip_blocks = 6
    
    forward_block_height = start_height
    backward_block_height = start_height - 1
    
    
    while not shutdown_flag:
        current_block_height = _bitcoin_node.get_current_block_height() - skip_blocks
        block_height = forward_block_height
        is_indexing_reverse = False
        
        if block_height > current_block_height: # if forward indexer has reached the latest block
            if backward_block_height == 0: # if finished reverse indexer, just wait for new blocks
                logger.info(
                    f"Waiting for new blocks. Current height is {current_block_height}"
                )
                time.sleep(10)
                continue
            else: # if has something to index in the reverser indexer, run reverse indexer
                logger.info(
                    f"Current height is {current_block_height}. Running reverse indexer while waiting for new blocks..."
                )
                block_height = backward_block_height
                is_indexing_reverse = True
        
        while _graph_indexer.check_if_block_is_indexed(block_height): # skip blocks already indexed
            logger.info(f"Skipping block #{block_height}. Already indexed.")
            block_height += -1 if is_indexing_reverse else 1

        if block_height == 0: # if backward indexer has reached the genesis, just continue
            backward_block_height = 0
            time.sleep(10)
            continue
        
        success = index_block(_bitcoin_node, _graph_indexer, _graph_search, block_height)        
        if success:
            if is_indexing_reverse:
                backward_block_height = block_height - 1
            else:
                forward_block_height = block_height + 1
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
    graph_indexer = GraphIndexer()
    graph_search = GraphSearch()
    
    smart_mode_str = os.getenv('BITCOIN_INDEXER_SMART_MODE', '0') or '0'
    start_height_str = os.getenv('BITCOIN_INDEXER_START_BLOCK_HEIGHT', None)
    end_height_str = os.getenv('BITCOIN_INDEXER_END_BLOCK_HEIGHT', '-1') or '-1'
    in_reverse_order_str = os.getenv('BITCOIN_INDEXER_IN_REVERSE_ORDER', '0') or '0'
    
    logger.info(in_reverse_order_str)
    
    if start_height_str is None:
        logger.info("Please specify BITCOIN_INDEXER_START_BLOCK_HEIGHT")
    else:
        smart_mode = int(smart_mode_str)
        start_height = int(start_height_str)
        end_height = int(end_height_str)
        in_reverse_order = int(in_reverse_order_str)

        logger.info("Starting indexer")
        
        logger.info("Creating indexes...")
        graph_indexer.create_indexes()
        
        logger.info("Syncing block range caches...")
        indexed_min_block_height, indexed_max_block_height = graph_search.get_min_max_block_height()
        graph_indexer.set_min_max_block_height_cache(indexed_min_block_height, indexed_max_block_height)
        logger.info(f"Indexed block height (min, max): [{indexed_min_block_height}, {indexed_max_block_height}]")

        if start_height > -1 and smart_mode: # if smart mode, run both forward and reverse indexer
            do_smart_indexing(bitcoin_node, graph_indexer, graph_search, start_height)
        elif start_height > -1 and end_height > -1: # if specifed both start and end, then iterate range
            iterate_range(bitcoin_node, graph_indexer, graph_search, start_height, end_height, bool(in_reverse_order))
        elif in_reverse_order: # if end is not specifed but in reverse order, then set end_height 1 and iterate range
            iterate_range(bitcoin_node, graph_indexer, graph_search, start_height, 1, bool(in_reverse_order))
        else: # if end_height and in_reverse_order are both unset, then move forward in real-time
            move_forward(bitcoin_node, graph_indexer, graph_search, start_height)
        
        graph_indexer.close()
        graph_search.close()
        logger.info("Indexer stopped")
