import os
import time
import signal
from neurons.setup_logger import setup_logger
from neurons.nodes.factory import NodeFactory
from neurons.nodes.bitcoin.node_utils import parse_block_data
from neurons.miners.bitcoin.balance_tracking.balance_indexer import BalanceIndexer

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

def index_block(_bitcoin_node, _balance_indexer, block_height):
    block = _bitcoin_node.get_block_by_height(block_height)
    num_transactions = len(block["tx"])
    start_time = time.time()
    block_data = parse_block_data(block)
    success = _balance_indexer.create_rows_focused_on_balance_changes(block_data, _bitcoin_node)
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
        
    return success


def move_forward(_bitcoin_node, _balance_indexer, start_block_height = 1):
    global shutdown_flag

    skip_blocks = 6
    block_height = start_block_height
    
    while not shutdown_flag:
        current_block_height = _bitcoin_node.get_current_block_height() - skip_blocks
        if block_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)
            continue
        
        success = index_block(_bitcoin_node, _balance_indexer, block_height)
        
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
    balance_indexer = BalanceIndexer()
    
    logger.info("Starting indexer")

    logger.info("Getting latest block number...")
    latest_block_height = balance_indexer.get_latest_block_number()
    logger.info(f"Latest block number is {latest_block_height}")
    
    move_forward(bitcoin_node, balance_indexer, latest_block_height + 1)

    balance_indexer.close()
    logger.info("Indexer stopped")
