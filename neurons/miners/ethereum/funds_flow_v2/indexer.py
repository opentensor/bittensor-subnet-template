import os
import signal
import time
from threading import Thread
from math import floor
from neurons.setup_logger import setup_logger
from neurons.nodes.evm.ethereum.node import EthereumNode
from neurons.miners.ethereum.funds_flow_v2.graph_creator import GraphCreator
from neurons.miners.ethereum.funds_flow_v2.graph_indexer import GraphIndexer
from neurons.miners.ethereum.funds_flow_v2.graph_search import GraphSearch

# Global flag to signal shutdown
shutdown_flag = False
CACHE_COUNT = 5000
tx = { 'cacheCnt': 0, 'cacheTx': [], 'inprogress': False }

logger = setup_logger("EthereumIndexer")

def shutdown_handler(signum, frame):
    global shutdown_flag
    logger.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True

def log_txHash_crashed_by_memgraph(transaction):
    transactionHash = ''
    for tx in transaction:
        transactionHash += tx.tx_hash + '\n'
    f = open(f"eth_crashed_block_by_memgraph.txt", "a")
    f.write(transactionHash)
    f.close()

def log_blockHeight_crashed_by_rpc(block_height):
    f = open("eth_crashed_block_by_rpc.txt", "a")
    f.write(f"{block_height}\n")
    f.close()

def log_finished_thread_info(index, start, last, time):
    f = open("eth_finished_thread.txt", "a")
    f.write(f"Index: {index}, Rage({start}, {last}), Total Spent Time: {time}\n")
    f.close()

def index_blocks(_graph_creator, _graph_indexer, _graph_search, start_height):
    global shutdown_flag
    ethereum_node = EthereumNode()
    skip_blocks = 6 # Set the number of block confirmations

    block_height = start_height
    start_time = time.time()

    while not shutdown_flag:
        current_block_height = ethereum_node.get_current_block_height() - 6
        buf_time = time.time()

        if current_block_height - skip_blocks < 0:
            logger.info(f"Waiting min {skip_blocks} for blocks to be mined.")
            time.sleep(3)
            continue

        if block_height > current_block_height:
            if tx['cacheCnt'] > CACHE_COUNT:
                tx['inprogress'] = True
                success = _graph_indexer.create_graph_focused_on_funds_flow(tx['cacheTx'])

                if success:
                    time_taken = time.time() - buf_time
                    formatted_tps = tx['cacheCnt'] / time_taken if time_taken > 0 else float("inf")
                    logger.info(f"[Main Thread] TPS: {formatted_tps}, Spent time: {time.time() - start_time}\n")
                else:
                    # sometimes we may have memgraph server connect issue catch all failed block so we can retry
                    log_txHash_crashed_by_memgraph(tx['cacheTx'])

                tx['cacheTx'].clear()
                tx['cacheCnt'] = 0
                buf_time = time.time()
                tx['inprogress'] = False

            continue

        while block_height <= current_block_height - skip_blocks:
            try:
                block = ethereum_node.get_block_by_height(block_height)
                if len(block["transactions"]) <= 0:
                    block_height += 1
                    continue

                in_memory_graph = _graph_creator.create_in_memory_graph_from_block(ethereum_node, block)
                newTransaction = in_memory_graph["block"].transactions
                newTransactionCnt = len(newTransaction)

                if newTransactionCnt <= 0:
                    block_height += 1
                    continue

                tx['cacheCnt'] += newTransactionCnt
                tx['cacheTx'] = tx['cacheTx'] + newTransaction

                if tx['cacheCnt'] > CACHE_COUNT:
                    tx['inprogress'] = True
                    success = _graph_indexer.create_graph_focused_on_funds_flow(tx['cacheTx'])

                    min_block_height_cache, max_block_height_cache = _graph_search.get_min_max_block_height_cache()
                    _graph_indexer.set_min_max_block_height_cache(min(min_block_height_cache, block_height), max(max_block_height_cache, block_height))

                    if success:
                        time_taken = time.time() - buf_time
                        formatted_tps = tx['cacheCnt'] / time_taken if time_taken > 0 else float("inf")
                        logger.info(f"[Main Thread] - Finished Block: {block_height}, TPS: {formatted_tps}, Spent time: {time.time() - start_time}\n")
                        
                    else:
                        # sometimes we may have memgraph server connect issue catch all failed block so we can retry
                        log_txHash_crashed_by_memgraph(0, tx['cacheTx'])

                    tx['cacheTx'].clear()
                    tx['cacheCnt'] = 0
                    buf_time = time.time()
                    tx['inprogress'] = False

                block_height += 1

                if shutdown_flag:
                    logger.info(f"Finished indexing block {block_height} before shutdown.")
                    break
            except Exception as e:
                print(e)
                # sometimes we may have rpc server connect issue catch all failed block so we can retry
                log_blockHeight_crashed_by_rpc(block_height)
                block_height += 1

def index_blocks_by_last_height(thread_index, _graph_creator, start, last):
    global shutdown_flag
    ethereum_node = EthereumNode()
    start_time = time.time()

    skip_blocks = 6 # Set the number of block confirmations
    index = thread_index + 1
    log_display = False

    block_height = start
    current_block_height = last - skip_blocks

    while block_height <= current_block_height and not shutdown_flag:
        try:
            inprogress_flag = tx["inprogress"]
            if inprogress_flag:
                if not log_display:
                    formatted_percent = "{:6.4f}".format(100 * (block_height - start)/(last - start))
                    logger.info(f"[Sub Thread {index}], from_height: {start}, to_height: {last}, Complete: {formatted_percent}%\n")
                    log_display = True
                time.sleep(0.01)
                continue
            else:
                log_display = False
                block = ethereum_node.get_block_by_height(block_height)
                if len(block["transactions"]) <= 0:
                    block_height += 1
                    continue

                in_memory_graph = _graph_creator.create_in_memory_graph_from_block(ethereum_node, block)
                newTransaction = in_memory_graph["block"].transactions
                newTransactionCnt = len(newTransaction)

                if newTransactionCnt <= 0:
                    block_height += 1
                    continue

                tx['cacheCnt'] += newTransactionCnt
                tx['cacheTx'] = tx['cacheTx'] + newTransaction
                block_height += 1

            if shutdown_flag:
                logger.info(f"Finished indexing block {block_height} before shutdown.")
                break
        except Exception as e:
            # sometimes we may have rpc server connect issue catch all failed block so we can retry
            log_blockHeight_crashed_by_rpc(block_height)
            block_height += 1

    log_finished_thread_info(index, start, last, time.time() - start_time)
    block_height += 1

    


# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()
    ethereum_node = EthereumNode()
    graph_search = GraphSearch()

    graph_indexer.create_indexes()

    retry_delay = 60

    # Latest START, LAST Block Height
    start_height = 0
    start_height_str = os.getenv('ETHEREUM_START_BLOCK_HEIGHT', None)
    last_height_str = os.getenv('ETHEREUM_LAST_BLOCK_HEIGHT', None)

    graph_last_block_height = graph_indexer.get_latest_block_number()
    if start_height_str is not None:
        start_height = int(start_height_str)
        if graph_last_block_height > start_height:
            start_height = graph_last_block_height + 1
    else:
        start_height = graph_last_block_height

    # Set Initial Min & Max, Block Height
    indexed_min_block_height, indexed_max_block_height = graph_search.get_min_max_block_height_cache()
    if indexed_min_block_height == 0:
        indexed_min_block_height = start_height
    graph_indexer.set_min_max_block_height_cache(indexed_min_block_height, indexed_max_block_height)

    current_block_height = ethereum_node.get_current_block_height()
    if last_height_str is not None:
        last_height = int(last_height_str)
        if current_block_height > last_height:
            last_height = current_block_height
    else:
        last_height = current_block_height

    # Config Sub Threads
    num_threads = 8 # set number of thread 8 by default
    num_thread_str = os.getenv('ETHEREUM_THREAD_CNT', None)
    if num_thread_str is not None:
        num_threads = int(num_thread_str)

    thread_depth = floor((last_height - start_height) / num_threads)
    restHeight = (last_height - start_height) - thread_depth * num_threads

    for i in range(num_threads):
        start = start_height + i * thread_depth
        last = start_height + (i + 1) * thread_depth - 1
        if i == num_threads - 1:
            last = start_height + (i + 1) * thread_depth + restHeight
        thread = Thread(target=index_blocks_by_last_height, args=(i, graph_creator, start, last))
        thread.start()

    # while True:
    try:
        logger.info('-- Main thread is running for indexing recent blocks --')
        index_blocks(graph_creator, graph_indexer, graph_search, last_height + 1)

    except Exception as e:
        ## traceback.print_exc()
        logger.error(f"Retry failed with error: {e}")
        logger.info(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)
        # break
    finally:
        graph_indexer.close()
        graph_search.close()
        logger.info("Indexer stopped")
