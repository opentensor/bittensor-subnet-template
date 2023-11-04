import signal
import time
import logging

from neurons.logging import setup_logger
from neurons.miners.bitcoin.bitcoin_node import BitcoinNode
from neurons.miners.bitcoin.configs import IndexerConfig
from neurons.miners.bitcoin.graph_indexer import GraphIndexer

# Global flag to signal shutdown
shutdown_flag = False
logger = setup_logger("BITCOIN INDEXER")


def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True


def index_blocks(_bitcoin_node, _graph_indexer):
    global shutdown_flag
    while not shutdown_flag:
        start_height = _graph_indexer.get_latest_block_number() + 1
        current_block_height = _bitcoin_node.get_current_block_height()

        if start_height > current_block_height:
            logger.info(
                f"Waiting for new blocks. Current height is {current_block_height}."
            )
            time.sleep(10)  # Wait for a minute before checking for new blocks
            continue

        for block_height in range(start_height, current_block_height + 1):
            transactions = _bitcoin_node.get_transactions_from_block_height(
                block_height
            )
            num_transactions = len(transactions)
            start_time = time.time()
            _graph_indexer.create_transaction_graph2([(block_height, transactions)])
            end_time = time.time()

            time_taken = end_time - start_time
            if time_taken > 0:
                tps = num_transactions / time_taken
                logger.info(
                    f"Block {block_height}: Processed {num_transactions} transactions in {time_taken:.2f} seconds ({tps:.2f} TPS)"
                )
            else:
                logger.info(
                    f"Block {block_height}: Processed {num_transactions} transactions in 0 seconds"
                )

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
    graph_indexer = GraphIndexer(config=indexer_config.graph_config)

    logger.info("Starting indexer")
    logger.info(f"Current config: {indexer_config}")
    logger.info(f"Current block height: {bitcoin_node.get_current_block_height()}")
    logger.info(f"Latest block height: {graph_indexer.get_latest_block_number()}")

    try:
        index_blocks(bitcoin_node, graph_indexer)
    except Exception as e:
        logger.error(f"Indexing failed with error: {e}")
    finally:
        graph_indexer.close()
        logger.info("Indexer stopped")
