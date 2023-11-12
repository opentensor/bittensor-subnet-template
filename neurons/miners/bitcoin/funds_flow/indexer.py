import signal
import time

from neurons.logging import setup_logger
from neurons.miners.bitcoin.node import BitcoinNode
from neurons.miners.configs import IndexerConfig
from neurons.miners.bitcoin.funds_flow.graph_creator import GraphCreator
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer

# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("BITCOIN INDEXER")


def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True


def index_blocks(_bitcoin_node, _graph_creator, _graph_indexer):
    global shutdown_flag

    while not shutdown_flag:
        start_height = _graph_indexer.get_latest_block_number() + 1
        current_block_height = _bitcoin_node.get_current_block_height()

        if start_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)
            continue

        block_height = start_height
        while block_height <= current_block_height:
            block = _bitcoin_node.get_block_by_height(block_height)
            num_transactions = len(block["tx"])
            start_time = time.time()
            in_memory_graph = _graph_creator.create_in_memory_graph_from_block(block)
            success = _graph_indexer.create_graph_focused_on_money_flow(in_memory_graph)
            end_time = time.time()
            time_taken = end_time - start_time
            node_block_height = bitcoin_node.get_current_block_height()
            progress = block_height / node_block_height * 100
            formatted_num_transactions = "{:>3}".format(num_transactions)
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
            else:
                logger.error(f"Failed to index block {block_height}.")
                time.sleep(30)

            if shutdown_flag:
                logger.info(f"Finished indexing block {block_height} before shutdown.")
                break


# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    indexer_config = IndexerConfig()
    bitcoin_node = BitcoinNode(config=indexer_config.node_config)
    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer(config=indexer_config.graph_config)

    logger.info("Starting indexer")
    logger.info(f"Current config: {indexer_config}")
    logger.info(f"Current node block height: {bitcoin_node.get_current_block_height()}")
    logger.info(
        f"Latest indexed block height: {graph_indexer.get_latest_block_number()}"
    )

    try:
        logger.info("Creating indexes...")
        graph_indexer.create_indexes()
        logger.info("Starting indexing blocks...")
        index_blocks(bitcoin_node, graph_creator, graph_indexer)
    except Exception as e:
        logger.error(f"Indexing failed with error: {e}")
    finally:
        graph_indexer.close()
        logger.info("Indexer stopped")
