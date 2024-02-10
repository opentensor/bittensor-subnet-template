import argparse
import os
import signal
import time
from neurons.setup_logger import setup_logger
from neurons.nodes.factory import NodeFactory
from neurons.miners.bitcoin.funds_flow.graph_creator import GraphCreator
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer

from insights.protocol import NETWORK_BITCOIN

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

    block_height = start_height
    while block_height >= end_height and not shutdown_flag:
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
        else:
            logger.error(f"Failed to index block {block_height}.")
            time.sleep(30)

        if shutdown_flag:
            logger.info(f"Finished indexing block {block_height} before shutdown.")
            break


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    start_height = int(os.getenv("BITCOIN_START_BLOCK_HEIGHT", 300))
    end_height = int(os.getenv("BITCOIN_END_BLOCK_HEIGHT", 200))
    bitcoin_node = NodeFactory.create_node(NETWORK_BITCOIN)
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()

    retry_delay = 60
    while not shutdown_flag:
        try:
            logger.info("Starting reverse indexer")
            graph_last_block_height = graph_indexer.get_latest_block_number()
            graph_min_block_height = graph_indexer.get_min_block_number()

            block_height_gaps = graph_indexer.find_gap_ranges_in_block_heights(start_height, end_height)

            logger.info(f"Currently Indexed Block Range: {graph_min_block_height} - {graph_last_block_height}")

            #if graph_min_block_height > 0 or graph_last_block_height > 0:
#                if graph_min_block_height <= end_height <= graph_last_block_height:
 #                   end_height = graph_last_block_height + 1
  #              if graph_min_block_height <= start_height <= graph_last_block_height:
   #                 start_height = graph_min_block_height - 1

            if start_height < end_height:
                break

            logger.info("Creating indexes...")
            graph_indexer.create_indexes()
            logger.info(f"Starting indexing blocks from {start_height} to {end_height}...")

            for range in block_height_gaps:
                index_blocks(bitcoin_node, graph_creator, graph_indexer, range[1], range[0])
        except Exception as e:
            logger.error(f"Indexing failed with error: {e}")
        finally:
            graph_indexer.close()
            logger.info("Indexer stopped")
            break