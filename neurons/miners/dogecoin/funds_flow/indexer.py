import os
import signal
import time
import traceback
from neurons.setup_logger import setup_logger
from neurons.nodes.bitcoin.node import BitcoinNode
from neurons.nodes.dogecoin.node import DogecoinNode
from neurons.miners.dogecoin.funds_flow.graph_creator import GraphCreator
from neurons.miners.dogecoin.funds_flow.graph_indexer import GraphIndexer


# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("Indexer")


def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True


def index_blocks(_bitcoin_node, _graph_creator, _graph_indexer, start_height):
    global shutdown_flag
    skip_blocks = 6

    while not shutdown_flag:
        current_block_height = _bitcoin_node.get_current_block_height() - 6
        if current_block_height - skip_blocks < 0:
            logger.info("Waiting min 6 for blocks to be mined.")
            time.sleep(10)
            continue

        if start_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)
            continue

        block_height = start_height
        while block_height <= current_block_height - skip_blocks:
            block = _bitcoin_node.get_block_by_height(block_height)
            num_transactions = len(block["tx"])
            start_time = time.time()
            in_memory_graph = _graph_creator.create_in_memory_graph_from_block(block)
            success = _graph_indexer.create_graph_focused_on_money_flow(in_memory_graph)
            end_time = time.time()
            time_taken = end_time - start_time
            node_block_height = _bitcoin_node.get_current_block_height()
            progress = block_height / node_block_height * 100
            formatted_num_transactions = "{:>4}".format(num_transactions)
            formatted_time_taken = "{:6.2f}".format(time_taken)
            formatted_tps = "{:8.2f}".format(
                num_transactions / time_taken if time_taken > 0 else float("inf")
            )
            formatted_progress = "{:6.2f}".format(progress)

            if time_taken > 0:
                logger.info(
                    "Block {:>6}: Processed {} transactions in {} seconds {} TPS Progress: {}%".format(
                        block_height,
                        formatted_num_transactions,
                        formatted_time_taken,
                        formatted_tps,
                        formatted_progress,
                    )
                )
            else:
                logger.info(
                    "Block {:>6}: Processed {} transactions in 0.00 seconds (  Inf TPS). Progress: {}%".format(
                        block_height, formatted_num_transactions, formatted_progress
                    )
                )

            if success:
                block_height += 1

                # indexer flooding prevention
                threshold = int(
                    os.getenv("BLOCK_PROCESSING_TRANSACTION_THRESHOLD", 500)
                )
                if num_transactions > threshold:
                    delay = float(os.getenv("BLOCK_PROCESSING_DELAY", 1))
                    logger.info(
                        f"Block tx count above {threshold}, slowing down indexing by {delay} seconds to prevent flooding."
                    )
                    time.sleep(delay)

            else:
                logger.error(f"Failed to index block {block_height}.")
                time.sleep(30)

            if shutdown_flag:
                logger.info(f"Finished indexing block {block_height} before shutdown.")
                break

            start_height += 1


# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    doge_node = DogecoinNode()
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()

    start_height_str = os.getenv("BITCOIN_START_BLOCK_HEIGHT", None)

    retry_delay = 60
    # purpose of this indexer is to index FROM to infinity only, indexing previous block range will be covered by another indexer - indexer_patch.py which will be slowly adding previous blocks to the graph
    while True:
        try:
            logger.info("Starting indexer")
            graph_last_block_height = graph_indexer.get_latest_block_number() + 1
            if start_height_str is not None:
                start_height = int(start_height_str)
                if graph_last_block_height > start_height:
                    start_height = graph_last_block_height
            else:
                start_height = graph_last_block_height

            logger.info(f"Starting from block height: {start_height}")
            logger.info(
                f"Current node block height: {doge_node.get_current_block_height()}"
            )
            logger.info(f"Latest indexed block height: {graph_last_block_height}")

            logger.info("Creating indexes...")
            graph_indexer.create_indexes()
            logger.info("Starting indexing blocks...")
            index_blocks(doge_node, graph_creator, graph_indexer, start_height)
            break
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Retry failed with error: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        finally:
            graph_indexer.close()
            logger.info("Indexer stopped")
