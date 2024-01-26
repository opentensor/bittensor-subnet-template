import os
import signal
import time
import traceback
from neurons.setup_logger import setup_logger
from neurons.nodes.factory import NodeFactory
from neurons.miners.bitcoin.funds_flow_v2.graph_creator import GraphCreator
from neurons.miners.bitcoin.funds_flow_v2.graph_indexer import GraphIndexer

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


def index_blocks(_bitcoin_node, _graph_creator, _graph_indexer, start_height, end_height):
    global shutdown_flag
    skip_blocks = 6

    while not shutdown_flag:
        # current_block_height = _bitcoin_node.get_current_block_height() - 6
        # if current_block_height - skip_blocks < 0:
        #     logger.info("Waiting min 6 for blocks to be mined.")
        #     time.sleep(10)
        #     continue

        # if start_height > current_block_height:
        #     logger.info(
        #         f"Waiting for new blocks. Current height is {current_block_height}."
        #     )
        #     time.sleep(10)
        #     continue

        block_height = start_height
        while block_height >= end_height:
            block = _bitcoin_node.get_block_by_height(block_height)
            num_transactions = len(block["tx"])
            start_time = time.time()
            in_memory_graph = _graph_creator.create_in_memory_graph_from_block(block)
            success = _graph_indexer.create_graph_focused_on_money_flow(in_memory_graph, _bitcoin_node)
            end_time = time.time()
            time_taken = end_time - start_time
            node_block_height = bitcoin_node.get_current_block_height()
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
                block_height -= 1

                # # indexer flooding prevention
                # threshold = int(os.getenv('BLOCK_PROCESSING_TRANSACTION_THRESHOLD', 500))
                # if num_transactions > threshold:
                #     delay = float(os.getenv('BLOCK_PROCESSING_DELAY', 1))
                #     logger.info(f"Block tx count above {threshold}, slowing down indexing by {delay} seconds to prevent flooding.")
                #     time.sleep(delay)

            else:
                logger.error(f"Failed to index block {block_height}.")
                time.sleep(30)

            if shutdown_flag:
                logger.info(f"Finished indexing block {block_height} before shutdown.")
                break

            # start_height += 1



# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    bitcoin_node = NodeFactory.create_node(NETWORK_BITCOIN)
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()

    start_height_str = os.getenv('BITCOIN_V2_START_BLOCK_HEIGHT', None)
    end_height_str = os.getenv('BITCOIN_V2_END_BLOCK_HEIGHT', None)
    
    if start_height_str is None or end_height_str is None:
        logger.info("Please specify BITCOIN_V2_START_BLOCK_HEIGHT and BITCOIN_V2_END_BLOCK_HEIGHT")
    else:
        start_height = int(start_height_str)
        end_height = int(end_height_str)

        retry_delay = 60
        # purpose of this indexer is to index FROM to infinity only, indexing previous block range will be covered by another indexer - indexer_patch.py which will be slowly adding previous blocks to the graph
        while True:
            try:
                logger.info("Starting indexer")
                graph_last_block_height = graph_indexer.get_latest_block_number()
                graph_min_block_height = graph_indexer.get_min_block_number()

                # logger.info(f"Starting from block height: {start_height}")
                # logger.info(f"Current node block height: {bitcoin_node.get_current_block_height()}")
                # logger.info(f"Latest indexed block height: {graph_last_block_height}")

                logger.info(f"Currently Indexed Block Range: {graph_min_block_height} - {graph_last_block_height}")

                if graph_min_block_height > 0 or graph_last_block_height > 0:
                    if end_height >= graph_min_block_height and end_height <= graph_last_block_height:
                        end_height = graph_last_block_height + 1
                    if start_height >= graph_min_block_height and start_height <= graph_last_block_height:
                        start_height = graph_min_block_height - 1
                        
                if start_height < end_height:
                    break

                logger.info("Creating indexes...")
                graph_indexer.create_indexes()
                logger.info(f"Starting indexing blocks from {start_height} to {end_height}...")
                
                index_blocks(bitcoin_node, graph_creator, graph_indexer, start_height, end_height)
            except Exception as e:
                ## traceback.print_exc()
                # logger.error(f"Retry failed with error: {e}")
                # logger.info(f"Retrying in {retry_delay} seconds...")
                # time.sleep(retry_delay)
                logger.error(f"Indexing failed with error: {e}")
            finally:
                graph_indexer.close()
                logger.info("Indexer stopped")
                break
