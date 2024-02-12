import os
import signal
import time
from threading import Thread
from math import floor
from neurons.setup_logger import setup_logger
from neurons.nodes.evm.ethereum.node import EthereumNode
from neurons.miners.ethereum.funds_flow.graph_creator import GraphCreator
from neurons.miners.ethereum.funds_flow.graph_indexer import GraphIndexer

# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("EthereumIndexer")

def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True

def index_blocks(tx, start_time, _ethereum_node, _graph_creator, _graph_indexer, start_height):
    global shutdown_flag
    skip_blocks = 6 # Set the number of block confirmations

    block_height = start_height

    while not shutdown_flag:
        current_block_height = _ethereum_node.get_current_block_height() - 6
        if current_block_height - skip_blocks < 0:
            logger.info(f"Waiting min {skip_blocks} for blocks to be mined.")
            time.sleep(10)
            continue

        if block_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)
            continue

        while block_height <= current_block_height - skip_blocks:
            try:
                block = _ethereum_node.get_block_by_height(block_height)
                if len(block["transactions"]) <= 0:
                    block_height += 1
                    continue

                in_memory_graph = _graph_creator.create_in_memory_graph_from_block(block)
                if len(in_memory_graph["block"].transactions) <= 0:
                    block_height += 1
                    continue

                success = _graph_indexer.create_graph_focused_on_funds_flow(in_memory_graph)

                if success:
                    tx['total_tx'] += len(in_memory_graph["block"].transactions)
                    time_taken = time.time() - start_time
                    formatted_tps = tx['total_tx'] / time_taken if time_taken > 0 else float("inf")
                    formatted_bps =  (block_height - start_height) / time_taken if time_taken > 0 else float("inf")
                    logger.info(f"[Main Thread] - Finished Block: {block_height}, Total TX: {tx['total_tx']}, TPS: {formatted_tps}, BPS: {formatted_bps}, Spent time: {time_taken}\n")
                    block_height += 1

                else:
                    # sometimes we may have rpc server connect issue catch all failed block so we can retry
                    f = open("crashed_block.txt", "a")
                    f.write('crashed block number - {}\n'.format(block_height))
                    f.close()
                    block_height += 1

                if shutdown_flag:
                    logger.info(f"Finished indexing block {block_height} before shutdown.")
                    break
            except Exception as e:
                # sometimes we may have rpc server connect issue catch all failed block so we can retry
                f = open("crashed_block.txt", "a")
                f.write('crashed block number - {}\n'.format(block_height))
                f.close()
                block_height += 1

# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    ethereum_node = EthereumNode()
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()

    num_threads = 8 # set number of thread 8 by default
    num_thread_str = os.getenv('ETHEREUM_THREAD_CNT', None)

    if num_thread_str is not None:
        num_threads = int(num_thread_str)

    retry_delay = 60

    start_height = 0

    start_height_str = os.getenv('ETHEREUM_START_BLOCK_HEIGHT', None)

    graph_last_block_height = int(str(graph_indexer.get_latest_block_number()), 16) + 1
    if start_height_str is not None:
        start_height = int(start_height_str)
        if graph_last_block_height > start_height:
            start_height = graph_last_block_height
    else:
        start_height = graph_last_block_height
    
    tx = {'total_tx': 0}
    start_time = time.time()

    logger.info("Starting indexer")
    logger.info(f"Starting from block height: {start_height}")
    logger.info(f"Latest indexed block height: {graph_last_block_height}")

    graph_indexer.create_indexes()

    # while True:
    try:
        logger.info("Creating indexes...")
        logger.info("Starting indexing blocks...")
        logger.info('-- Main thread is running for indexing recent blocks --')

        index_blocks(tx, start_time, ethereum_node, graph_creator, graph_indexer, start_height)

    except Exception as e:
        ## traceback.print_exc()
        logger.error(f"Retry failed with error: {e}")
        logger.info(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)
        # break
    finally:
        graph_indexer.close()
        logger.info("Indexer stopped")
