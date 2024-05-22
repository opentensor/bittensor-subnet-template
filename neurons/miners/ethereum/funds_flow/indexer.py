import os
import signal
import time
from threading import Thread
from math import floor
from neurons.setup_logger import setup_logger
from neurons.nodes.evm.ethereum.node import EthereumNode
from neurons.miners.ethereum.funds_flow.graph_creator import GraphCreator
from neurons.miners.ethereum.funds_flow.graph_indexer import GraphIndexer
from neurons.miners.ethereum.funds_flow.graph_search import GraphSearch

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

# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

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

def single_index(_graph_creator, _graph_indexer, _graph_search, start_height: int, end_height: int, is_reverse_order: bool = False):
    global shutdown_flag
    ethereum_node = EthereumNode()

    start = start_height
    last = end_height
    direction = 1

    if not is_reverse_order:
        start = start_height if start_height < end_height else end_height
        last = end_height if end_height > start_height else start_height
    else:
        start = start_height if start_height > end_height else end_height
        last = end_height if end_height < start_height else start_height
        direction = -1

    start_time = time.time()
    buf_time = time.time()

    while not shutdown_flag and (last - start) * direction >= 0:
        try:
            block = ethereum_node.get_block_by_height(start)
            if len(block["transactions"]) <= 0:
                start += direction
                continue

            in_memory_graph = _graph_creator.create_in_memory_graph_from_block(ethereum_node, block)
            newTransaction = in_memory_graph["block"].transactions
            newTransactionCnt = len(newTransaction)

            if newTransactionCnt <= 0:
                start += direction
                continue

            tx['cacheCnt'] += newTransactionCnt
            tx['cacheTx'] = tx['cacheTx'] + newTransaction

            if tx['cacheCnt'] > CACHE_COUNT or (last - start) * direction == 0:
                tx['inprogress'] = True
                success = _graph_indexer.create_graph_focused_on_funds_flow(tx['cacheTx'])

                min_block_height_cache, max_block_height_cache = _graph_search.get_min_max_block_height_cache()
                _graph_indexer.set_min_max_block_height_cache(min(min_block_height_cache, start), max(max_block_height_cache, start))

                if success:
                    time_taken = time.time() - buf_time
                    formatted_tps = tx['cacheCnt'] / time_taken if time_taken > 0 else float("inf")
                    logger.info(f"[Main Thread]", finished_block = start, tps = formatted_tps, spent_time = time.time() - start_time)
                    
                else:
                    # sometimes we may have memgraph server connect issue catch all failed block so we can retry
                    log_txHash_crashed_by_memgraph(0, tx['cacheTx'])

                tx['cacheTx'].clear()
                tx['cacheCnt'] = 0
                buf_time = time.time()
                tx['inprogress'] = False

            start += direction

            if shutdown_flag:
                logger.info(f"Finished indexing block before shutdown.", block = start)
                break
        except Exception as e:
            # sometimes we may have rpc server connect issue catch all failed block so we can retry
            log_blockHeight_crashed_by_rpc(start)
            start += direction
    
    logger.info(f"Finished Single Main Indexing", start_block = start_height, end_block = end_height)
    log_finished_thread_info(0, start_height, end_height, time.time() - start_time)

def index_blocks(_graph_creator, _graph_indexer, _graph_search, start_height):
    global shutdown_flag
    ethereum_node = EthereumNode()
    skip_blocks = 6 # Set the number of block confirmations

    block_height = start_height
    start_time = time.time()

    while not shutdown_flag:
        current_block_height = ethereum_node.get_current_block_height() - skip_blocks
        buf_time = time.time()

        if current_block_height - skip_blocks < 0:
            logger.info(f"Waiting for blocks to be mined.", skip_blocks = skip_blocks)
            time.sleep(3)
            continue

        if block_height > current_block_height:
            if tx['cacheCnt'] > CACHE_COUNT:
                tx['inprogress'] = True
                success = _graph_indexer.create_graph_focused_on_funds_flow(tx['cacheTx'])

                if success:
                    time_taken = time.time() - buf_time
                    formatted_tps = tx['cacheCnt'] / time_taken if time_taken > 0 else float("inf")
                    logger.info(f"[Main Thread]", tps = formatted_tps, spent_time = time.time() - start_time)
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
                        logger.info(f"[Main Thread]", finished_block = start, tps = formatted_tps, spent_time = time.time() - start_time)
                        
                    else:
                        # sometimes we may have memgraph server connect issue catch all failed block so we can retry
                        log_txHash_crashed_by_memgraph(0, tx['cacheTx'])

                    tx['cacheTx'].clear()
                    tx['cacheCnt'] = 0
                    buf_time = time.time()
                    tx['inprogress'] = False

                block_height += 1

                if shutdown_flag:
                    logger.info(f"Finished indexing block before shutdown.", block_height = block_height)
                    break
            except Exception as e:
                # sometimes we may have rpc server connect issue catch all failed block so we can retry
                log_blockHeight_crashed_by_rpc(block_height)
                block_height += 1

def index_blocks_by_last_height(thread_index, _graph_creator, start, last):
    global shutdown_flag
    ethereum_node = EthereumNode()
    start_time = time.time()

    index = thread_index + 1
    log_display = False

    block_height = start
    current_block_height = last

    while block_height <= current_block_height and not shutdown_flag:
        try:
            inprogress_flag = tx["inprogress"]
            if inprogress_flag:
                if not log_display:
                    formatted_percent = "{:6.4f}".format(100 * (block_height - start)/(last - start))
                    logger.info(f"[Sub Thread]", thread_index = index, start_block = start, last_block = last, completed_percent = formatted_percent)
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
                logger.info(f"Finished indexing block before shutdown.", block = block_height)
                break
        except Exception as e:
            # sometimes we may have rpc server connect issue catch all failed block so we can retry
            log_blockHeight_crashed_by_rpc(block_height)
            block_height += 1

    log_finished_thread_info(index, start, last, time.time() - start_time)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    graph_creator = GraphCreator()
    graph_indexer = GraphIndexer()
    ethereum_node = EthereumNode()
    graph_search = GraphSearch()

    graph_indexer.create_indexes()

    retry_delay = 60

    # Latest SUB Thread START, LAST Block Height
    sub_start_height = 0
    sub_last_height = 0
    sub_start_height_str = os.getenv('ETHEREUM_SUB_START_BLOCK_HEIGHT', None)
    sub_last_height_str = os.getenv('ETHEREUM_SUB_END_BLOCK_HEIGHT', None)

    graph_last_block_height = graph_indexer.get_latest_block_number()
    if sub_start_height_str:
        sub_start_height = int(sub_start_height_str)
        if graph_last_block_height > sub_start_height:
            sub_start_height = graph_last_block_height + 1
    else:
        sub_start_height = graph_last_block_height

    # Set Initial SUB Thread Min & Max Block Height
    indexed_min_block_height, indexed_max_block_height = graph_search.get_min_max_block_height_cache()
    if indexed_min_block_height == 0:
        indexed_min_block_height = sub_start_height
    graph_indexer.set_min_max_block_height_cache(indexed_min_block_height, indexed_max_block_height)

    current_block_height = ethereum_node.get_current_block_height()
    if sub_last_height_str:
        sub_last_height = int(sub_last_height_str)
        if current_block_height > sub_last_height:
            sub_last_height = current_block_height
    else:
        sub_last_height = current_block_height

    # Config Sub Threads
    num_threads = 8 # set number of thread 8 by default
    num_thread_str = os.getenv('ETHEREUM_SUB_THREAD_CNT', None)
    if num_thread_str:
        num_threads = int(num_thread_str)
    
    # Config Main Thread
    main_start_height = 0
    main_last_height = 0
    is_reverse_order = False
    main_start_height_str = os.getenv('ETHEREUM_MAIN_START_BLOCK_HEIGHT', None)
    main_last_height_str = os.getenv('ETHEREUM_MAIN_END_BLOCK_HEIGHT', None)
    is_reverse_order_str = os.getenv('ETHEREUM_MAIN_IN_REVERSE_ORDER', None)

    if main_start_height_str:
        main_start_height = int(main_start_height_str)
    if main_last_height_str:
        main_last_height = int(main_last_height_str)
    if is_reverse_order_str:
        is_reverse_order = bool(int(is_reverse_order_str))

    try:
        # Main Indexer running with Multi Sub Indexers
        if num_threads > 0 and sub_start_height > 0 and sub_last_height > 0:
            thread_depth = floor((sub_last_height - sub_start_height) / num_threads)
            restHeight = (sub_last_height - sub_start_height) - thread_depth * num_threads

            num_threads = 1 if thread_depth == 0 else num_threads

            for i in range(num_threads):
                start = sub_start_height + i * thread_depth
                last = sub_start_height + (i + 1) * thread_depth - 1
                if i == num_threads - 1:
                    last = sub_start_height + (i + 1) * thread_depth + restHeight
                thread = Thread(target=index_blocks_by_last_height, args=(i, graph_creator, start, last))
                thread.start()
            
            logger.info('-- Main thread is running for indexing recent blocks --')
            index_blocks(graph_creator, graph_indexer, graph_search, sub_last_height + 1)

        # Only Main Indexer running
        else:
            if main_start_height > 0 and main_last_height > 0:
                logger.info(f'-- Main thread is running for indexing based on range of block numbers --', min_block = main_start_height, max_block = main_last_height)
                single_index(graph_creator, graph_indexer, graph_search, main_start_height, main_last_height, is_reverse_order)
            else:
                logger.error('ETHEREUM_MAIN_START_BLOCK_HEIGHT & ETHEREUM_MAIN_END_BLOCK_HEIGHT should be given by ENV')

    except Exception as e:
        logger.error(f"Retry failed with error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})
        logger.info(f"Retrying in seconds...", retry_delay = retry_delay)
        time.sleep(retry_delay)
    finally:
        graph_indexer.close()
        graph_search.close()
        logger.info("Indexer stopped")
